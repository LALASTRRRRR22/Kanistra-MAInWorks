using AetherChronicles.Data;
using AetherChronicles.Entities;
using AetherChronicles.Systems;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using System;
using System.Collections.Generic;
using System.Linq;

namespace AetherChronicles.UI
{
    public class HUD
    {
        private readonly SpriteBatch _sb;
        private readonly SpriteFont _font;
        private readonly SpriteFont _bigFont;
        private readonly GraphicsDevice _gd;
        private Texture2D _pixel = null!;

        private readonly List<(string msg, float timer, Color color)> _notifications = new();

        public HUD(SpriteBatch sb, SpriteFont font, SpriteFont bigFont, GraphicsDevice gd)
        {
            _sb = sb;
            _font = font;
            _bigFont = bigFont;
            _gd = gd;
            CreatePixel();
        }

        private void CreatePixel()
        {
            _pixel = new Texture2D(_gd, 1, 1);
            _pixel.SetData(new[] { Color.White });
        }

        public void AddNotification(string msg, Color color)
        {
            _notifications.Insert(0, (msg, 3.5f, color));
            if (_notifications.Count > 5) _notifications.RemoveAt(_notifications.Count - 1);
        }

        public void Update(float dt)
        {
            for (int i = _notifications.Count - 1; i >= 0; i--)
            {
                var n = _notifications[i];
                n.timer -= dt;
                _notifications[i] = n;
                if (n.timer <= 0) _notifications.RemoveAt(i);
            }
        }

        public void Draw(Player player, QuestSystem quests, float dayTime, bool bossVisible, float bossHealthPct)
        {
            int w = _gd.Viewport.Width, h = _gd.Viewport.Height;

            _sb.Begin(SpriteSortMode.Deferred, BlendState.AlphaBlend);

            // Health bar (bottom left)
            DrawBar(20, h - 90, 220, 24, player.Stats.HealthPercent,
                new Color(180, 30, 30), new Color(50, 10, 10), "HP");
            // XP bar
            DrawBar(20, h - 58, 220, 18, player.Stats.ExpPercent,
                new Color(100, 180, 255), new Color(20, 40, 80), "XP");

            // Player info
            DrawPanel(20, h - 130, 220, 35);
            _sb.DrawString(_font, $"Lv.{player.Stats.Level}  Knight", new Vector2(30, h - 125), Color.Gold);

            // Gold
            DrawPanel(260, h - 90, 120, 24);
            _sb.DrawString(_font, $"Gold: {player.Gold}", new Vector2(270, h - 88), Color.Gold);

            // Potions count
            int potions = player.Inventory.Where(i => i.Type == ItemType.Potion).Sum(i => i.Quantity);
            DrawPanel(260, h - 58, 120, 18);
            _sb.DrawString(_font, $"Potions: {potions}", new Vector2(270, h - 58), new Color(100, 255, 100));

            // Active quests (top right)
            int qx = w - 280, qy = 20;
            DrawPanel(qx - 5, qy - 5, 275, 30);
            _sb.DrawString(_font, "QUESTS", new Vector2(qx, qy), Color.Gold);
            qy += 30;

            foreach (var q in quests.ActiveQuests.Take(3))
            {
                DrawPanel(qx - 5, qy - 2, 275, 20 + q.Objectives.Count * 18);
                _sb.DrawString(_font, q.Title, new Vector2(qx, qy), Color.White);
                qy += 18;
                foreach (var obj in q.Objectives)
                {
                    Color objColor = obj.IsComplete ? Color.LimeGreen : new Color(200, 200, 200);
                    _sb.DrawString(_font, $"  {obj.Description}: {obj.Progress}", new Vector2(qx, qy), objColor);
                    qy += 16;
                }
                qy += 4;
            }

            // Boss health bar
            if (bossVisible)
            {
                int bw = 500, bh = 28;
                int bx = (w - bw) / 2, by = h - 120;
                DrawPanel(bx - 5, by - 25, bw + 10, 60);
                _sb.DrawString(_font, "CRYSTAL DRAGON", new Vector2(bx + 160, by - 22), new Color(100, 200, 255));
                DrawBar(bx, by, bw, bh, bossHealthPct, new Color(100, 200, 255), new Color(20, 40, 80), "");
            }

            // Minimap (bottom right)
            DrawMinimap(w - 175, h - 175, player, 150);

            // Day/Night indicator
            string timeStr = GetTimeString(dayTime);
            DrawPanel(w / 2 - 50, 8, 100, 22);
            _sb.DrawString(_font, timeStr, new Vector2(w / 2 - 40, 10), Color.White);

            // Notifications (left side)
            for (int i = 0; i < _notifications.Count; i++)
            {
                var n = _notifications[i];
                float alpha = Math.Min(1f, n.timer);
                var col = n.color * alpha;
                _sb.DrawString(_font, n.msg, new Vector2(25, 20 + i * 22), col);
            }

            // Controls hint
            DrawPanel(w - 220, h - 55, 215, 48);
            _sb.DrawString(_font, "WASD: Move  | LMB: Attack", new Vector2(w - 215, h - 52), new Color(180,180,180));
            _sb.DrawString(_font, "E: Roll | F: Potion | I: Inventory", new Vector2(w - 215, h - 34), new Color(180,180,180));

            _sb.End();
        }

        public void DrawDamageNumbers(IEnumerable<CombatEvent> events, Matrix view, Matrix projection)
        {
            int w = _gd.Viewport.Width, h = _gd.Viewport.Height;
            _sb.Begin(SpriteSortMode.Deferred, BlendState.AlphaBlend);

            foreach (var evt in events)
            {
                float alpha = Math.Min(1f, evt.Timer);
                var screenPos = _gd.Viewport.Project(evt.Position, projection, view, Matrix.Identity);
                if (screenPos.Z < 0 || screenPos.Z > 1) continue;

                float offset = (1f - evt.Timer * 0.5f) * 30f;
                _sb.DrawString(_font, evt.Message,
                    new Vector2(screenPos.X - 20, screenPos.Y - offset),
                    evt.Color * alpha);
            }

            _sb.End();
        }

        private void DrawBar(int x, int y, int w, int h, float pct, Color fillColor, Color bgColor, string label)
        {
            DrawRect(x, y, w, h, bgColor);
            DrawRect(x, y, (int)(w * Math.Max(0f, Math.Min(1f, pct))), h, fillColor);
            DrawRect(x, y, w, h, new Color(0, 0, 0, 100), false); // border
            if (label.Length > 0)
                _sb.DrawString(_font, label, new Vector2(x + 5, y + 2), Color.White);
        }

        private void DrawPanel(int x, int y, int w, int h)
        {
            DrawRect(x, y, w, h, new Color(0, 0, 0, 140));
            DrawRect(x, y, w, h, new Color(80, 80, 100, 80), false);
        }

        private void DrawRect(int x, int y, int w, int h, Color color, bool fill = true)
        {
            if (fill)
                _sb.Draw(_pixel, new Rectangle(x, y, w, h), color);
            else
            {
                _sb.Draw(_pixel, new Rectangle(x, y, w, 1), color);
                _sb.Draw(_pixel, new Rectangle(x, y + h - 1, w, 1), color);
                _sb.Draw(_pixel, new Rectangle(x, y, 1, h), color);
                _sb.Draw(_pixel, new Rectangle(x + w - 1, y, 1, h), color);
            }
        }

        private void DrawMinimap(int x, int y, Player player, int size)
        {
            DrawRect(x, y, size, size, new Color(0, 0, 0, 160));
            DrawRect(x, y, size, size, new Color(60, 100, 60, 80), false);

            // Player dot
            int px = x + size / 2, py = y + size / 2;
            DrawRect(px - 3, py - 3, 6, 6, Color.White);
            _sb.DrawString(_font, "N", new Vector2(x + size / 2 - 5, y + 2), new Color(200,200,200));
        }

        private string GetTimeString(float dayTime)
        {
            int hour = (int)(dayTime * 24);
            int min = (int)((dayTime * 24 - hour) * 60);
            string ampm = hour >= 12 ? "PM" : "AM";
            if (hour > 12) hour -= 12;
            if (hour == 0) hour = 12;
            return $"{hour:D2}:{min:D2} {ampm}";
        }
    }
}
