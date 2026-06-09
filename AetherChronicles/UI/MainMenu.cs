using AetherChronicles.Data;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using System;

namespace AetherChronicles.UI
{
    public enum MenuAction { None, NewGame, Continue, Quit }

    public class MainMenu
    {
        private readonly SpriteBatch _sb;
        private readonly SpriteFont _font;
        private readonly SpriteFont _bigFont;
        private readonly GraphicsDevice _gd;
        private Texture2D _pixel = null!;
        private int _selectedIndex;
        private readonly bool _hasSave;
        private float _animTime;
        private float[] _buttonYOffsets;

        public MenuAction Action { get; private set; } = MenuAction.None;

        private readonly string[] _menuItems;

        public MainMenu(SpriteBatch sb, SpriteFont font, SpriteFont bigFont, GraphicsDevice gd)
        {
            _sb = sb; _font = font; _bigFont = bigFont; _gd = gd;
            _hasSave = SaveSystem.HasSave();

            _menuItems = _hasSave
                ? new[] { "New Game", "Continue", "Quit" }
                : new[] { "New Game", "Quit" };

            _buttonYOffsets = new float[_menuItems.Length];

            CreatePixel();
        }

        private void CreatePixel()
        {
            _pixel = new Texture2D(_gd, 1, 1);
            _pixel.SetData(new[] { Color.White });
        }

        public void Update(float dt, Engine.InputManager input)
        {
            Action = MenuAction.None;
            _animTime += dt;

            for (int i = 0; i < _buttonYOffsets.Length; i++)
            {
                float targetY = i == _selectedIndex ? -3f : 0f;
                _buttonYOffsets[i] += (targetY - _buttonYOffsets[i]) * dt * 12f;
            }

            if (input.JustPressed(Microsoft.Xna.Framework.Input.Keys.Up))
            {
                _selectedIndex = (_selectedIndex - 1 + _menuItems.Length) % _menuItems.Length;
            }
            if (input.JustPressed(Microsoft.Xna.Framework.Input.Keys.Down))
            {
                _selectedIndex = (_selectedIndex + 1) % _menuItems.Length;
            }
            if (input.JustPressed(Microsoft.Xna.Framework.Input.Keys.Enter) ||
                input.JustPressed(Microsoft.Xna.Framework.Input.Keys.Space))
            {
                SelectCurrent();
            }
        }

        private void SelectCurrent()
        {
            string item = _menuItems[_selectedIndex];
            Action = item switch
            {
                "New Game" => MenuAction.NewGame,
                "Continue" => MenuAction.Continue,
                "Quit"     => MenuAction.Quit,
                _ => MenuAction.None
            };
        }

        public void Draw()
        {
            int w = _gd.Viewport.Width, h = _gd.Viewport.Height;

            _sb.Begin(SpriteSortMode.Deferred, BlendState.AlphaBlend);

            // Dark overlay
            _sb.Draw(_pixel, new Rectangle(0, 0, w, h), new Color(10, 5, 20));

            // Animated stars
            var rng = new Random(42);
            for (int i = 0; i < 200; i++)
            {
                float x = rng.Next(0, w);
                float y = rng.Next(0, h / 2);
                float twinkle = MathF.Sin(_animTime * 2f + i * 0.3f) * 0.5f + 0.5f;
                _sb.Draw(_pixel, new Rectangle((int)x, (int)y, 2, 2),
                    Color.White * twinkle * 0.8f);
            }

            // Title glow
            float titlePulse = MathF.Sin(_animTime * 1.5f) * 0.15f + 0.85f;
            string title = "AETHER CHRONICLES";
            string subtitle = "Rise of the Crystal Dragon";

            var titleSize = _bigFont.MeasureString(title);
            var subSize = _font.MeasureString(subtitle);

            // Title shadow
            _sb.DrawString(_bigFont, title,
                new Vector2((w - titleSize.X) / 2 + 3, 98), new Color(30, 10, 80) * titlePulse);
            // Title
            _sb.DrawString(_bigFont, title,
                new Vector2((w - titleSize.X) / 2, 95),
                Color.Lerp(new Color(150, 100, 255), new Color(100, 200, 255), titlePulse));

            // Subtitle
            _sb.DrawString(_font, subtitle,
                new Vector2((w - subSize.X) / 2, 150), new Color(200, 180, 255) * 0.9f);

            // Decorative line
            _sb.Draw(_pixel, new Rectangle(w / 2 - 200, 178, 400, 2), new Color(100, 80, 200, 180));

            // Menu items
            int btnW = 280, btnH = 50;
            int startY = h / 2 - (_menuItems.Length * (btnH + 15)) / 2;

            for (int i = 0; i < _menuItems.Length; i++)
            {
                bool selected = i == _selectedIndex;
                int btnX = (w - btnW) / 2;
                int btnY = startY + i * (btnH + 15) + (int)_buttonYOffsets[i];

                // Button shadow
                _sb.Draw(_pixel, new Rectangle(btnX + 4, btnY + 4, btnW, btnH),
                    new Color(0, 0, 0, 120));

                // Button background
                var bgColor = selected
                    ? Color.Lerp(new Color(60, 30, 120), new Color(80, 50, 180),
                        MathF.Sin(_animTime * 3f) * 0.5f + 0.5f)
                    : new Color(20, 15, 40);
                _sb.Draw(_pixel, new Rectangle(btnX, btnY, btnW, btnH), bgColor);

                // Button border
                Color borderColor = selected ? new Color(160, 120, 255) : new Color(80, 60, 120);
                _sb.Draw(_pixel, new Rectangle(btnX, btnY, btnW, 2), borderColor);
                _sb.Draw(_pixel, new Rectangle(btnX, btnY + btnH - 2, btnW, 2), borderColor);
                _sb.Draw(_pixel, new Rectangle(btnX, btnY, 2, btnH), borderColor);
                _sb.Draw(_pixel, new Rectangle(btnX + btnW - 2, btnY, 2, btnH), borderColor);

                // Button text
                var textSize = _font.MeasureString(_menuItems[i]);
                Color textColor = selected ? Color.White : new Color(180, 160, 220);
                if (selected)
                {
                    // Glow effect
                    _sb.DrawString(_font, _menuItems[i],
                        new Vector2((w - textSize.X) / 2 + 1, btnY + (btnH - textSize.Y) / 2 + 1),
                        new Color(100, 80, 200, 100));
                }
                _sb.DrawString(_font, _menuItems[i],
                    new Vector2((w - textSize.X) / 2, btnY + (btnH - textSize.Y) / 2), textColor);

                // Selection arrow
                if (selected)
                    _sb.DrawString(_font, ">", new Vector2(btnX + 15, btnY + (btnH - textSize.Y) / 2),
                        new Color(200, 180, 255));
            }

            // Version / copyright
            _sb.DrawString(_font, "v1.0.0  |  Use Arrow Keys + Enter to navigate",
                new Vector2(10, h - 25), new Color(100, 100, 120));

            _sb.End();
        }
    }
}
