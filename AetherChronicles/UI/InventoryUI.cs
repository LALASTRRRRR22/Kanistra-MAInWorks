using AetherChronicles.Data;
using AetherChronicles.Entities;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using System.Collections.Generic;

namespace AetherChronicles.UI
{
    public class InventoryUI
    {
        private readonly SpriteBatch _sb;
        private readonly SpriteFont _font;
        private readonly GraphicsDevice _gd;
        private Texture2D _pixel = null!;
        private int _selectedSlot = 0;

        public InventoryUI(SpriteBatch sb, SpriteFont font, GraphicsDevice gd)
        {
            _sb = sb; _font = font; _gd = gd;
            _pixel = new Texture2D(gd, 1, 1);
            _pixel.SetData(new[] { Color.White });
        }

        public void Update(Engine.InputManager input, Player player)
        {
            int count = player.Inventory.Count;
            if (count == 0) return;

            if (input.JustPressed(Microsoft.Xna.Framework.Input.Keys.Left))
                _selectedSlot = (_selectedSlot - 1 + count) % count;
            if (input.JustPressed(Microsoft.Xna.Framework.Input.Keys.Right))
                _selectedSlot = (_selectedSlot + 1) % count;

            // Use/Equip item
            if (input.JustPressed(Microsoft.Xna.Framework.Input.Keys.Enter))
            {
                if (_selectedSlot < count)
                {
                    var item = player.Inventory[_selectedSlot];
                    if (item.Type == ItemType.Weapon) player.EquipWeapon(item);
                    else if (item.Type == ItemType.Armor) player.EquipArmor(item);
                    else if (item.Type == ItemType.Potion) player.UsePotion();
                }
            }
        }

        public void Draw(Player player)
        {
            int w = _gd.Viewport.Width, h = _gd.Viewport.Height;

            _sb.Begin(SpriteSortMode.Deferred, BlendState.AlphaBlend);

            // Background
            _sb.Draw(_pixel, new Rectangle(0, 0, w, h), new Color(0, 0, 0, 180));

            int panelW = 700, panelH = 500;
            int px = (w - panelW) / 2, py = (h - panelH) / 2;

            // Panel
            DrawPanel(px, py, panelW, panelH);
            _sb.DrawString(_font, "INVENTORY", new Vector2(px + 20, py + 15), Color.Gold);
            _sb.DrawString(_font, $"Gold: {player.Gold}", new Vector2(px + panelW - 150, py + 15), Color.Gold);

            // Stats panel
            _sb.DrawString(_font, "Character Stats", new Vector2(px + 20, py + 55), Color.White);
            _sb.DrawString(_font, $"Level: {player.Stats.Level}", new Vector2(px + 20, py + 80), Color.LightGray);
            _sb.DrawString(_font, $"HP: {(int)player.Stats.CurrentHealth}/{player.Stats.MaxHealth}", new Vector2(px + 20, py + 100), new Color(255, 100, 100));
            _sb.DrawString(_font, $"Attack: {player.Stats.TotalAttack}", new Vector2(px + 20, py + 120), new Color(255, 200, 100));
            _sb.DrawString(_font, $"Defense: {player.Stats.TotalDefense}", new Vector2(px + 20, py + 140), new Color(100, 200, 255));

            // Equipped
            var weapon = ItemDatabase.GetById(player.EquippedWeaponId);
            var armor = ItemDatabase.GetById(player.EquippedArmorId);
            _sb.DrawString(_font, "Equipped:", new Vector2(px + 20, py + 170), Color.Gold);
            if (weapon != null)
                _sb.DrawString(_font, $"  Weapon: {weapon.Name}", new Vector2(px + 20, py + 190),
                    ItemData.GetRarityColor(weapon.Rarity));
            if (armor != null)
                _sb.DrawString(_font, $"  Armor: {armor.Name}", new Vector2(px + 20, py + 210),
                    ItemData.GetRarityColor(armor.Rarity));

            // Inventory grid
            int gridX = px + 200, gridY = py + 55;
            int slotSize = 80, cols = 5;
            _sb.DrawString(_font, "Items (← → to select, Enter to use/equip)", new Vector2(gridX, gridY - 22), new Color(200,200,200));

            for (int i = 0; i < player.Inventory.Count; i++)
            {
                var item = player.Inventory[i];
                int col = i % cols, row = i / cols;
                int sx = gridX + col * (slotSize + 8);
                int sy = gridY + row * (slotSize + 8);

                bool selected = i == _selectedSlot;

                // Slot background
                _sb.Draw(_pixel, new Rectangle(sx, sy, slotSize, slotSize),
                    selected ? new Color(60, 50, 100) : new Color(30, 25, 50));

                // Rarity border
                var rarityColor = ItemData.GetRarityColor(item.Rarity);
                _sb.Draw(_pixel, new Rectangle(sx, sy, slotSize, 2), rarityColor);
                _sb.Draw(_pixel, new Rectangle(sx, sy + slotSize - 2, slotSize, 2), rarityColor);
                _sb.Draw(_pixel, new Rectangle(sx, sy, 2, slotSize), rarityColor);
                _sb.Draw(_pixel, new Rectangle(sx + slotSize - 2, sy, 2, slotSize), rarityColor);

                // Item color square
                _sb.Draw(_pixel, new Rectangle(sx + 10, sy + 10, 30, 30), item.Color);

                // Item name (short)
                string shortName = item.Name.Length > 10 ? item.Name[..10] + "..." : item.Name;
                _sb.DrawString(_font, shortName, new Vector2(sx + 2, sy + slotSize - 22), Color.White);
                if (item.Quantity > 1)
                    _sb.DrawString(_font, $"x{item.Quantity}", new Vector2(sx + slotSize - 25, sy + 5), Color.Yellow);
            }

            // Item detail
            if (_selectedSlot < player.Inventory.Count)
            {
                var item = player.Inventory[_selectedSlot];
                int dx = px + 200, dy = py + 320;
                DrawPanel(dx, dy, panelW - 220, 130);
                _sb.DrawString(_font, item.Name, new Vector2(dx + 10, dy + 10),
                    ItemData.GetRarityColor(item.Rarity));
                _sb.DrawString(_font, item.Rarity.ToString(), new Vector2(dx + 10, dy + 30),
                    ItemData.GetRarityColor(item.Rarity) * 0.8f);
                _sb.DrawString(_font, item.Description, new Vector2(dx + 10, dy + 50), Color.LightGray);
                if (item.AttackBonus > 0)
                    _sb.DrawString(_font, $"+{item.AttackBonus} ATK", new Vector2(dx + 10, dy + 70), new Color(255, 200, 100));
                if (item.DefenseBonus > 0)
                    _sb.DrawString(_font, $"+{item.DefenseBonus} DEF", new Vector2(dx + 10, dy + 90), new Color(100, 200, 255));
                if (item.HealAmount > 0)
                    _sb.DrawString(_font, $"Heals {item.HealAmount} HP", new Vector2(dx + 10, dy + 90), new Color(100, 255, 100));

                string action = item.Type switch
                {
                    ItemType.Weapon => "Press Enter to Equip",
                    ItemType.Armor => "Press Enter to Equip",
                    ItemType.Potion => "Press Enter to Use",
                    _ => ""
                };
                if (action.Length > 0)
                    _sb.DrawString(_font, action, new Vector2(dx + 10, dy + 110), Color.Gold);
            }

            _sb.DrawString(_font, "Press I or Escape to close", new Vector2(px + 20, py + panelH - 25), new Color(150, 150, 150));

            _sb.End();
        }

        private void DrawPanel(int x, int y, int w, int h)
        {
            _sb.Draw(_pixel, new Rectangle(x, y, w, h), new Color(15, 12, 30, 220));
            _sb.Draw(_pixel, new Rectangle(x, y, w, 2), new Color(80, 60, 120));
            _sb.Draw(_pixel, new Rectangle(x, y + h - 2, w, 2), new Color(80, 60, 120));
            _sb.Draw(_pixel, new Rectangle(x, y, 2, h), new Color(80, 60, 120));
            _sb.Draw(_pixel, new Rectangle(x + w - 2, y, 2, h), new Color(80, 60, 120));
        }
    }
}
