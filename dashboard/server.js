require('dotenv').config();
const express = require('express');
const bodyParser = require('body-parser');
const { Client, GatewayIntentBits, Partials, EmbedBuilder, ActionRowBuilder, StringSelectMenuBuilder, StringSelectMenuOptionBuilder } = require('discord.js');
const Database = require('better-sqlite3');
const app = express();
const PORT = 3000;

// Init Bot Discord
const bot = new Client({
    intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMessages],
    partials: [Partials.Channel]
});
const TOKEN = process.env.DISCORD_TOKEN;
bot.login(TOKEN);

// Init Database
const db = new Database('./database.db');
db.prepare(`CREATE TABLE IF NOT EXISTS embeds (id INTEGER PRIMARY KEY AUTOINCREMENT, channel TEXT, title TEXT, description TEXT, date TEXT)`).run();
db.prepare(`CREATE TABLE IF NOT EXISTS giveaways (id INTEGER PRIMARY KEY AUTOINCREMENT, channel TEXT, prize TEXT, winners INTEGER, duration INTEGER, date TEXT)`).run();
try { db.prepare('ALTER TABLE giveaways ADD COLUMN winner TEXT').run(); } catch (e) {}
db.prepare(`CREATE TABLE IF NOT EXISTS reaction_roles (id INTEGER PRIMARY KEY AUTOINCREMENT,channel TEXT,title TEXT,description TEXT,roles TEXT,date TEXT)`).run();

// EJS & Body Parser
app.set('view engine', 'ejs');
app.set('views', './views');
app.use(bodyParser.urlencoded({ extended: true }));

let isLoggedIn = false;

// Pages du panel
app.get('/login', (req, res) => res.render('login', { error: null }));
app.post('/login', (req, res) => { isLoggedIn = req.body.password === process.env.PANEL_PASSWORD; res.redirect(isLoggedIn ? '/' : '/login'); });
app.get('/logout', (req, res) => { isLoggedIn = false; res.redirect('/login'); });
app.get('/', (req, res) => isLoggedIn ? res.render('index') : res.redirect('/login'));
app.get('/giveaway', (req, res) => isLoggedIn ? res.render('giveaway') : res.redirect('/login'));
app.get('/reaction-roles', (req, res) => isLoggedIn ? res.render('reaction_roles') : res.redirect('/login'));

// Récupération des salons et rôles
app.get('/channels', (req, res) => {
    const guild = bot.guilds.cache.first();
    if (!guild) return res.status(404).send([]);
    const channels = guild.channels.cache.sort((a, b) => a.rawPosition - b.rawPosition).map(c => ({ id: c.id, name: c.name, type: c.type, parentId: c.parentId }));
    res.json(channels);
});
app.get('/roles', (req, res) => {
    const guild = bot.guilds.cache.first();
    if (!guild) return res.status(404).send([]);
    const roles = guild.roles.cache.filter(r => r.name !== "@everyone").sort((a, b) => b.position - a.position).map(r => ({ id: r.id, name: r.name }));
    res.json(roles);
});

// Envoi d'Embed
app.post('/send-embed', async (req, res) => {
    const { title, description, channel } = req.body;
    const targetChannel = await bot.channels.fetch(channel);
    if (!targetChannel) return res.send("❌ Salon introuvable.");

    const embed = new EmbedBuilder().setTitle(title).setDescription(description).setColor(0x0099ff);
    await targetChannel.send({ embeds: [embed] });

    db.prepare('INSERT INTO embeds (channel, title, description, date) VALUES (?, ?, ?, ?)').run(channel, title, description, new Date().toISOString());
    res.send("✅ Embed envoyé avec succès !");
});

// Lancer un Giveaway
app.post('/start-giveaway', async (req, res) => {
    const { channel, duration, winners, prize } = req.body;
    const targetChannel = await bot.channels.fetch(channel);
    if (!targetChannel) return res.send("❌ Salon introuvable.");

    const embed = new EmbedBuilder().setTitle("🎉 Giveaway 🎉").setDescription(`**Prix :** ${prize}\n**Temps :** ${duration} minutes\nCliquez sur 🎉 pour participer !`).setColor(0xFFD700);
    const message = await targetChannel.send({ embeds: [embed] });
    await message.react('🎉');

    const stmt = db.prepare('INSERT INTO giveaways (channel, prize, winners, duration, date) VALUES (?, ?, ?, ?, ?)');
    const info = stmt.run(channel, prize, parseInt(winners), parseInt(duration), new Date().toISOString());
    const giveawayId = info.lastInsertRowid;

    res.send("✅ Giveaway lancé avec succès !");

    setTimeout(async () => {
        const updatedMessage = await targetChannel.messages.fetch(message.id);
        const reaction = updatedMessage.reactions.cache.get('🎉');
        if (!reaction) return targetChannel.send("🎉 Giveaway terminé. Aucun participant.");

        const users = await reaction.users.fetch();
        const participants = users.filter(u => !u.bot);
        if (participants.size === 0) return targetChannel.send("🎉 Giveaway terminé. Aucun participant.");

        const winnersCount = Math.min(parseInt(winners), participants.size);
        const winnerArray = participants.random(winnersCount);
        const winnerIds = winnerArray.map(u => u.id).join(',');
        const winnerMentions = winnerArray.map(u => `<@${u.id}>`).join(', ');

        await targetChannel.send(`🎉 Félicitations à ${winnerMentions} pour avoir gagné **${prize}** !`);
        db.prepare('UPDATE giveaways SET winner = ? WHERE id = ?').run(winnerIds, giveawayId);
    }, parseInt(duration) * 60000);
});

// Reaction Roles
app.post('/send-reaction-roles', async (req, res) => {
    const { channel, title, description, roles } = req.body;
    const roleIds = Array.isArray(roles) ? roles : [roles];
    const targetChannel = await bot.channels.fetch(channel);
    db.prepare('INSERT INTO reaction_roles (channel, title, description, roles, date) VALUES (?, ?, ?, ?, ?)').run(channel,title,description,Array.isArray(roles) ? roles.join(',') : roles,new Date().toISOString());
    if (!targetChannel) return res.send("❌ Salon introuvable.");

    const embed = new EmbedBuilder().setTitle(title).setDescription(description).setColor(0x00FF00);
    const options = roleIds.map(roleId => {
        const role = bot.guilds.cache.first().roles.cache.get(roleId);
        return { label: role ? role.name : "Inconnu", value: roleId };
    });

    const selectMenu = new StringSelectMenuBuilder().setCustomId('reaction_roles').setPlaceholder('Sélectionnez vos rôles').setMinValues(1).setMaxValues(options.length).addOptions(options.map(opt => new StringSelectMenuOptionBuilder().setLabel(opt.label).setValue(opt.value)));
    const row = new ActionRowBuilder().addComponents(selectMenu);
    await targetChannel.send({ embeds: [embed], components: [row] });
    res.send("✅ Reaction Roles envoyé avec succès !");
});

// Historique Embeds
app.get('/history', (req, res) => {
    if (!isLoggedIn) return res.redirect('/login');
    const rows = db.prepare('SELECT * FROM embeds ORDER BY id DESC').all();
    const enrichedRows = rows.map(embed => {
        const channel = bot.channels.cache.get(embed.channel);
        return { ...embed, channelName: channel ? channel.name : `Salon inconnu (${embed.channel})` };
    });
    res.render('history', { embeds: enrichedRows });
});

// Historique Giveaways avec Top Gagnants
app.get('/giveaway-history', (req, res) => {
    if (!isLoggedIn) return res.redirect('/login');

    const rows = db.prepare('SELECT * FROM giveaways ORDER BY id DESC').all();

    const enrichedRows = rows.map(giveaway => {
        const channel = bot.channels.cache.get(giveaway.channel);
        const channelName = channel ? channel.name : `Salon inconnu (${giveaway.channel})`;

        const winnerIds = giveaway.winner ? giveaway.winner.match(/\d+/g) || [] : [];
        const winnerNames = winnerIds.map(id => {
            const member = bot.guilds.cache.first()?.members.cache.get(id);
            return member ? `${member.user.username}#${member.user.discriminator}` : `<@${id}>`;
        });
        const winnerDisplay = winnerNames.length > 0 ? winnerNames.join(', ') : 'Non tiré';

        return { ...giveaway, channelName, winnerDisplay, winnerIds };
    });

    const winnerCounts = {};
    enrichedRows.forEach(giveaway => {
        giveaway.winnerIds.forEach(id => {
            const member = bot.guilds.cache.first()?.members.cache.get(id);
            const displayName = member ? `${member.user.username}#${member.user.discriminator}` : `<@${id}>`;
            winnerCounts[displayName] = (winnerCounts[displayName] || 0) + 1;
        });
    });

    const sorted = Object.entries(winnerCounts).sort((a, b) => b[1] - a[1]).slice(0, 10);
    const topWinners = sorted.map(([name, count]) => ({ name, count }));

    res.render('giveaway_history', { giveaways: enrichedRows, topWinners });
});

// Gestion des interactions Reaction Roles
const { MessageFlags } = require('discord-api-types/v10');
bot.on('interactionCreate', async (interaction) => {
    if (!interaction.isStringSelectMenu()) return;
    if (interaction.customId !== 'reaction_roles') return;

    const member = await interaction.guild.members.fetch(interaction.user.id);
    const selectedRoles = interaction.values;
    const rolesToAdd = selectedRoles.map(roleId => interaction.guild.roles.cache.get(roleId)).filter(Boolean);

    try {
        await member.roles.add(rolesToAdd);
        await interaction.reply({ content: '✅ Vos rôles ont été attribués avec succès !', flags: MessageFlags.Ephemeral });
    } catch (err) {
        console.error(err);
        await interaction.reply({ content: '❌ Une erreur est survenue lors de l\'attribution des rôles.', flags: MessageFlags.Ephemeral });
    }
});

//Historique des interactions Reaction Roles
app.get('/reaction-roles-history', (req, res) => {
    if (!isLoggedIn) return res.redirect('/login');

    const rows = db.prepare('SELECT * FROM reaction_roles ORDER BY id DESC').all();

    const enrichedRows = rows.map(record => {
        const channel = bot.channels.cache.get(record.channel);
        const channelName = channel ? channel.name : `Salon inconnu (${record.channel})`;

        const roleIds = record.roles.split(',');
        const roleNames = roleIds.map(id => {
            const role = bot.guilds.cache.first()?.roles.cache.get(id);
            return role ? role.name : `Rôle inconnu (${id})`;
        });

        return { ...record, channelName, roleNames };
    });

    res.render('reaction_roles_history', { records: enrichedRows });
});

// Lancer le Dashboard
app.listen(PORT, () => console.log(`✅ Dashboard en ligne sur http://localhost:${PORT}`));
