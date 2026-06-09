using AetherChronicles.Data;
using AetherChronicles.Engine;
using AetherChronicles.Entities;
using AetherChronicles.Models;
using AetherChronicles.Rendering;
using AetherChronicles.Systems;
using AetherChronicles.UI;
using AetherChronicles.World;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Microsoft.Xna.Framework.Input;
using System;
using System.Collections.Generic;

namespace AetherChronicles
{
    public class AetherGame : Game
    {
        private readonly GraphicsDeviceManager _graphics;
        private SpriteBatch _spriteBatch = null!;
        private BasicEffect _basicEffect = null!;

        // Fonts
        private SpriteFont _font = null!;
        private SpriteFont _bigFont = null!;

        // Engine
        private readonly GameStateManager _stateManager = new();
        private readonly InputManager _input = new();
        private Camera3D _camera = null!;

        // Game systems
        private GameWorld _world = null!;
        private CombatSystem _combat = null!;
        private QuestSystem _quests = null!;
        private readonly ParticleSystem _particles = new(3000);

        // Entities
        private Player _player = null!;
        private GameModel _playerModel = null!;

        // UI
        private HUD _hud = null!;
        private MainMenu _mainMenu = null!;
        private InventoryUI _inventoryUI = null!;

        // Game state


        private float _gameOverTimer;
        private float _saveTimer;

        private float _screenShake;
        private float _screenShakeX, _screenShakeY;
        private readonly Random _rng = new();

        // Dropped items in the world
        private readonly List<(Vector3 pos, ItemData item)> _droppedItems = new();

        public AetherGame()
        {
            _graphics = new GraphicsDeviceManager(this)
            {
                PreferredBackBufferWidth = 1280,
                PreferredBackBufferHeight = 720,
                PreferMultiSampling = true,
                SynchronizeWithVerticalRetrace = true
            };
            Content.RootDirectory = "Content";
            IsMouseVisible = true;
            Window.Title = "Aether Chronicles — Rise of the Crystal Dragon";
            Window.AllowUserResizing = false;
        }

        protected override void Initialize()
        {
            _camera = new Camera3D(_graphics.PreferredBackBufferWidth / (float)_graphics.PreferredBackBufferHeight);
            base.Initialize();
        }

        protected override void LoadContent()
        {
            _spriteBatch = new SpriteBatch(GraphicsDevice);
            _basicEffect = new BasicEffect(GraphicsDevice);

            // Load fonts from ContentManager (built via MonoGame Pipeline)
            try
            {
                _font = Content.Load<SpriteFont>("Fonts/GameFont");
                _bigFont = Content.Load<SpriteFont>("Fonts/TitleFont");
            }
            catch
            {
                // Fallback: create a basic font texture if content not found
                _font = CreateDefaultFont();
                _bigFont = _font;
            }

            InitGame(false);
        }

        private void InitGame(bool loadSave)
        {
            _world = new GameWorld(GraphicsDevice, 12345);
            _world.LoadModels();
            _world.Generate();

            _playerModel = ModelFactory.CreateKnight(GraphicsDevice);
            _player = new Player(_input) { Position = Vector3.Zero, Model = _playerModel };

            // Give starter items
            var starterWeapon = ItemDatabase.GetById(1)!;
            var starterArmor = ItemDatabase.GetById(4)!;
            _player.AddItem(starterWeapon);
            _player.AddItem(starterArmor);
            _player.EquipWeapon(starterWeapon);
            _player.EquipArmor(starterArmor);
            _player.Gold = 50;

            // Start potions
            var potion = ItemDatabase.GetById(7)!;
            potion.Quantity = 2;
            _player.AddItem(potion);

            if (loadSave)
            {
                var save = SaveSystem.Load();
                if (save != null)
                {
                    _player.Stats.Level = save.Level;
                    _player.Stats.Experience = save.Experience;
                    _player.Stats.CurrentHealth = save.Health;
                    _player.Gold = save.Gold;
                    _player.Position = new Vector3(save.PlayerX, 0, save.PlayerZ);
                }
            }

            _quests = new QuestSystem();
            _quests.OnQuestComplete += quest =>
            {
                _hud?.AddNotification($"Quest Complete: {quest.Title}!", Color.Gold);
                _player.Gold += quest.RewardGold;
                _hud?.AddNotification($"+{quest.RewardGold} Gold rewarded!", Color.Gold);
                if (quest.RewardItemId.HasValue)
                {
                    var reward = ItemDatabase.GetById(quest.RewardItemId.Value);
                    if (reward != null) _player.AddItem(reward);
                }
            };
            _quests.OnQuestStarted += quest =>
            {
                _hud?.AddNotification($"New Quest: {quest.Title}", new Color(100, 200, 255));
            };

            _player.OnLevelUp += lvl =>
            {
                _hud?.AddNotification($"Level Up! You are now Level {lvl}!", Color.Gold);
            };
            _player.OnPickupItem += name =>
            {
                _hud?.AddNotification($"Picked up: {name}", Color.LimeGreen);
            };

            _combat = new CombatSystem(_particles);

            _hud = new HUD(_spriteBatch, _font, _bigFont, GraphicsDevice);
            _inventoryUI = new InventoryUI(_spriteBatch, _font, GraphicsDevice);
            _mainMenu = new MainMenu(_spriteBatch, _font, _bigFont, GraphicsDevice);
        }

        protected override void Update(GameTime gameTime)
        {
            float dt = (float)gameTime.ElapsedGameTime.TotalSeconds;
            _input.Update();

            if (_input.JustPressed(Keys.Escape))
            {
                if (_stateManager.Current == GameState.Playing ||
                    _stateManager.Current == GameState.Inventory)
                    _stateManager.Change(GameState.MainMenu);
                else if (_stateManager.Current == GameState.MainMenu)
                    Exit();
            }

            switch (_stateManager.Current)
            {
                case GameState.MainMenu:
                    UpdateMainMenu(dt);
                    break;
                case GameState.Playing:
                    UpdateGame(gameTime, dt);
                    break;
                case GameState.Inventory:
                    _inventoryUI.Update(_input, _player);
                    if (_input.JustPressed(Keys.I) || _input.JustPressed(Keys.Escape))
                        _stateManager.Change(GameState.Playing);
                    break;
                case GameState.GameOver:
                    _gameOverTimer -= dt;
                    if (_input.JustPressed(Keys.Enter) || _gameOverTimer <= 0)
                        _stateManager.Change(GameState.MainMenu);
                    break;
                case GameState.Victory:
                    if (_input.JustPressed(Keys.Enter))
                        _stateManager.Change(GameState.MainMenu);
                    break;
            }

            base.Update(gameTime);
        }

        private void UpdateMainMenu(float dt)
        {
            _mainMenu.Update(dt, _input);
            switch (_mainMenu.Action)
            {
                case MenuAction.NewGame:
                    InitGame(false);
                    _stateManager.Change(GameState.Playing);
                    break;
                case MenuAction.Continue:
                    InitGame(true);
                    _stateManager.Change(GameState.Playing);
                    break;
                case MenuAction.Quit:
                    Exit();
                    break;
            }
        }

        private void UpdateGame(GameTime gameTime, float dt)
        {
            // Screen shake decay
            if (_screenShake > 0)
            {
                _screenShake -= dt * 8f;
                _screenShakeX = (float)(_rng.NextDouble() * 2 - 1) * _screenShake;
                _screenShakeY = (float)(_rng.NextDouble() * 2 - 1) * _screenShake;
            }
            else { _screenShakeX = 0; _screenShakeY = 0; }

            // Player movement
            var moveDir = _player.GetMovementInput(_camera.Yaw);
            Velocity moveVelocity = new Velocity { Value = moveDir };

            var newPos = _player.Position + moveDir * dt;
            if (!_world.CheckCollision(newPos, 0.5f))
                _player.Position = newPos;

            _player.Update(gameTime);

            // Player attack
            if (_input.MouseLeftJustPressed)
            {
                var allEnemies = new List<Entity>(_world.Enemies);
                if (_world.Boss != null && _world.Boss.IsAlive) allEnemies.Add(_world.Boss);
                bool hit = _combat.PlayerAttack(_player, allEnemies);
                if (hit) _screenShake = MathF.Min(_screenShake + 0.15f, 0.5f);
            }

            // Dodge
            if (_input.JustPressed(Keys.E))
            {
                _player.TryDodge(moveDir.LengthSquared() > 0.01f ? moveDir : Vector3.Zero);
            }

            // Inventory
            if (_input.JustPressed(Keys.I))
                _stateManager.Change(GameState.Inventory);

            // Potion
            if (_input.JustPressed(Keys.F))
            {
                _player.UsePotion();
                _particles.Emit(ParticleEffect.Heal, _player.Position + Vector3.Up);
            }

            // Camera
            _camera.Update(_player.Position, gameTime);

            // World update
            _world.Update(gameTime, _player);

            // Enemy attacks on player
            foreach (var entity in _world.Enemies)
            {
                if (entity is Enemy enemy && enemy.IsAlive && enemy.IsActive)
                {
                    float dist = Vector3.Distance(enemy.Position, _player.Position);
                    if (enemy.State == EnemyState.Attack && dist <= enemy.Stats.AttackRange + 0.5f)
                    {
                        float prevHp = _player.Stats.CurrentHealth;
                        _combat.EnemyAttackPlayer(enemy, _player);
                        if (_player.Stats.CurrentHealth < prevHp)
                            _screenShake = MathF.Min(_screenShake + 0.3f, 1.0f);
                    }
                }
            }

            // Boss attacks
            if (_world.Boss != null && _world.Boss.IsAlive)
            {
                var boss = _world.Boss;
                float bossToPlayer = Vector3.Distance(boss.Position, _player.Position);

                if (boss.State == EnemyState.Attack && bossToPlayer <= boss.Stats.AttackRange + 1f)
                {
                    float prevHp = _player.Stats.CurrentHealth;
                    _combat.EnemyAttackPlayer(boss, _player);
                    if (_player.Stats.CurrentHealth < prevHp)
                        _screenShake = MathF.Min(_screenShake + 0.5f, 1.5f);
                }

                // Check breath projectiles
                foreach (var proj in boss.BreathProjectiles)
                {
                    if (_combat.CheckProjectileHit(proj, _player))
                        _screenShake = MathF.Min(_screenShake + 0.4f, 1.0f);
                }
            }

            // Dark mage projectiles
            foreach (var entity in _world.Enemies)
            {
                if (entity is DarkMageEnemy mage && mage.IsAlive)
                {
                    foreach (var proj in mage.Projectiles)
                        _combat.CheckProjectileHit(proj, _player);
                }
            }

            // Process deaths
            var deadEnemies = new List<Enemy>();
            foreach (var entity in _world.Enemies)
            {
                if (entity is Enemy e && !e.IsAlive && e.IsActive)
                    deadEnemies.Add(e);
            }
            foreach (var dead in deadEnemies)
            {
                int xp = _combat.ProcessEnemyDeath(dead, _player);
                _quests.OnEnemyKilled(dead.Type);
                TryDropItem(dead);
            }

            // Boss death
            if (_world.Boss != null && !_world.Boss.IsAlive && _world.Boss.IsActive)
            {
                _combat.ProcessEnemyDeath(_world.Boss, _player);
                _quests.OnEnemyKilled(EntityType.DragonBoss);
                _world.Boss.IsActive = false;
                _screenShake = 3f;
                _stateManager.Change(GameState.Victory);
            }

            // Item pickup
            for (int i = _droppedItems.Count - 1; i >= 0; i--)
            {
                var (pos, item) = _droppedItems[i];
                if (Vector3.Distance(_player.Position, pos) < 1.5f)
                {
                    _player.AddItem(item);
                    if (item.Type == ItemType.Potion) _quests.OnItemPickup(ItemType.Potion);
                    _droppedItems.RemoveAt(i);
                }
            }

            // Player death
            if (!_player.IsAlive)
            {
                _stateManager.Change(GameState.GameOver);
                _gameOverTimer = 5f;
            }

            // Particles
            _particles.Update(dt);

            // HUD
            _hud.Update(dt);
            _combat.Update(dt);

            // Auto-save every 60 seconds
            _saveTimer += dt;
            if (_saveTimer >= 60f)
            {
                _saveTimer = 0;
                AutoSave();
            }

            base.Update(gameTime);
        }

        private void TryDropItem(Enemy enemy)
        {
            float dropChance = enemy.Type switch
            {
                EntityType.Goblin => 0.3f,
                EntityType.OrcWarrior => 0.5f,
                EntityType.DarkMage => 0.6f,
                _ => 0.4f
            };

            if (_rng.NextDouble() < dropChance)
            {
                int itemId = enemy.Type switch
                {
                    EntityType.Goblin => _rng.Next(0, 2) == 0 ? 7 : 10,
                    EntityType.OrcWarrior => _rng.Next(0, 3) switch { 0 => 2, 1 => 5, _ => 7 },
                    EntityType.DarkMage => _rng.Next(0, 2) == 0 ? 8 : 7,
                    _ => 7
                };
                var item = ItemDatabase.GetById(itemId);
                if (item != null)
                    _droppedItems.Add((enemy.Position, item));
            }
        }

        protected override void Draw(GameTime gameTime)
        {
            switch (_stateManager.Current)
            {
                case GameState.MainMenu:
                    GraphicsDevice.Clear(new Color(10, 5, 20));
                    _mainMenu.Draw();
                    break;

                case GameState.Playing:
                case GameState.Inventory:
                    DrawGame(gameTime);
                    if (_stateManager.Current == GameState.Inventory)
                        _inventoryUI.Draw(_player);
                    break;

                case GameState.GameOver:
                    DrawGame(gameTime);
                    DrawGameOver();
                    break;

                case GameState.Victory:
                    DrawGame(gameTime);
                    DrawVictory();
                    break;
            }

            base.Draw(gameTime);
        }

        private void DrawGame(GameTime gameTime)
        {
            GraphicsDevice.Clear(_world.SkyColor);
            GraphicsDevice.DepthStencilState = DepthStencilState.Default;
            GraphicsDevice.BlendState = BlendState.Opaque;
            GraphicsDevice.RasterizerState = RasterizerState.CullCounterClockwise;

            var view = Matrix.CreateTranslation(_screenShakeX, _screenShakeY, 0) * _camera.View;
            var projection = _camera.Projection;

            // Draw terrain
            _world.Terrain.Draw(_basicEffect, view, projection);

            // Draw world objects
            _world.DrawObjects(_basicEffect, view, projection);

            // Draw enemies
            _world.DrawEnemies(_basicEffect, view, projection);

            // Draw boss
            if (_world.Boss != null && _world.Boss.IsAlive && _world.Boss.IsActive)
            {
                DrawDragon(view, projection);
            }

            // Draw mage projectiles
            foreach (var entity in _world.Enemies)
            {
                if (entity is DarkMageEnemy mage && mage.IsAlive)
                    DrawProjectiles(mage.Projectiles, new Color(120, 0, 200), view, projection);
            }

            // Draw boss breath
            if (_world.Boss != null)
                DrawProjectiles(_world.Boss.BreathProjectiles, new Color(100, 200, 255), view, projection);

            // Draw dropped items
            DrawDroppedItems(view, projection, (float)gameTime.TotalGameTime.TotalSeconds);

            // Draw player
            _player.Draw(_basicEffect, view, projection);

            // Particles
            GraphicsDevice.BlendState = BlendState.Additive;
            GraphicsDevice.DepthStencilState = DepthStencilState.DepthRead;
            _particles.Draw(GraphicsDevice, _basicEffect, view, projection);
            GraphicsDevice.BlendState = BlendState.Opaque;
            GraphicsDevice.DepthStencilState = DepthStencilState.Default;

            // HUD
            bool bossVisible = _world.Boss != null && _world.Boss.IsAlive &&
                Vector3.Distance(_player.Position, _world.Boss.Position) < 50f;
            float bossHpPct = _world.Boss != null ? _world.Boss.Stats.HealthPercent : 0f;
            _hud.Draw(_player, _quests, _world.DayTime, bossVisible, bossHpPct);
            _hud.DrawDamageNumbers(_combat.Events, view, projection);
        }

        private void DrawDragon(Matrix view, Matrix projection)
        {
            var boss = _world.Boss!;
            float wingFlap = MathF.Sin(boss.WingFlapAngle) * 0.3f;

            // Animate wings
            if (boss.Model != null && boss.Model.Parts.Count > 6)
            {
                // Wings are parts 5 and 6
                boss.Model.Parts[5].LocalTransform =
                    Matrix.CreateRotationZ(0.4f + wingFlap) * Matrix.CreateTranslation(-3.5f, 3.5f + wingFlap * 0.5f, 0.5f);
                boss.Model.Parts[6].LocalTransform =
                    Matrix.CreateRotationZ(-0.4f - wingFlap) * Matrix.CreateTranslation(3.5f, 3.5f + wingFlap * 0.5f, 0.5f);
            }

            boss.Draw(_basicEffect, view, projection);
        }

        private void DrawProjectiles(
            System.Collections.Generic.List<MagicProjectile> projs,
            Color color, Matrix view, Matrix projection)
        {
            _basicEffect.View = view;
            _basicEffect.Projection = projection;
            _basicEffect.LightingEnabled = false;
            _basicEffect.VertexColorEnabled = true;

            foreach (var proj in projs)
            {
                if (!proj.Active) continue;
                float t = proj.Life / 3f;
                float s = 0.2f;
                var pos = proj.Position;
                var verts = new[]
                {
                    new VertexPositionColor(pos + new Vector3(-s,-s, 0), color),
                    new VertexPositionColor(pos + new Vector3( s,-s, 0), color),
                    new VertexPositionColor(pos + new Vector3( s, s, 0), color),
                    new VertexPositionColor(pos + new Vector3(-s, s, 0), color),
                };
                _basicEffect.World = Matrix.Identity;
                foreach (var pass in _basicEffect.CurrentTechnique.Passes)
                {
                    pass.Apply();
                    GraphicsDevice.DrawUserPrimitives(PrimitiveType.TriangleList, new[]
                    {
                        verts[0], verts[1], verts[2], verts[0], verts[2], verts[3]
                    }, 0, 2);
                }
            }
        }

        private void DrawDroppedItems(Matrix view, Matrix projection, float time)
        {
            _basicEffect.View = view;
            _basicEffect.Projection = projection;
            _basicEffect.LightingEnabled = false;
            _basicEffect.VertexColorEnabled = true;

            foreach (var (pos, item) in _droppedItems)
            {
                float bob = MathF.Sin(time * 2f) * 0.15f;
                var itemPos = pos + Vector3.Up * (0.5f + bob);
                float s = 0.25f;
                var col = item.Color;
                var verts = new[]
                {
                    new VertexPositionColor(itemPos + new Vector3(-s,-s, 0), col),
                    new VertexPositionColor(itemPos + new Vector3( s,-s, 0), col),
                    new VertexPositionColor(itemPos + new Vector3( s, s, 0), col),
                    new VertexPositionColor(itemPos + new Vector3(-s, s, 0), col),
                };
                _basicEffect.World = Matrix.CreateRotationY(time);
                foreach (var pass in _basicEffect.CurrentTechnique.Passes)
                {
                    pass.Apply();
                    GraphicsDevice.DrawUserPrimitives(PrimitiveType.TriangleList, new[]
                    {
                        verts[0], verts[1], verts[2], verts[0], verts[2], verts[3]
                    }, 0, 2);
                }
            }
        }

        private void DrawGameOver()
        {
            int w = GraphicsDevice.Viewport.Width, h = GraphicsDevice.Viewport.Height;
            _spriteBatch.Begin(SpriteSortMode.Deferred, BlendState.AlphaBlend);

            var pixel = new Texture2D(GraphicsDevice, 1, 1);
            pixel.SetData(new[] { Color.White });
            _spriteBatch.Draw(pixel, new Rectangle(0, 0, w, h), new Color(0, 0, 0, 180));

            string msg = "YOU HAVE FALLEN";
            string sub = "Press Enter to return to menu";
            var ms = _bigFont.MeasureString(msg);
            var ss = _font.MeasureString(sub);

            _spriteBatch.DrawString(_bigFont, msg, new Vector2((w - ms.X) / 2, h / 2 - 60), new Color(200, 50, 50));
            _spriteBatch.DrawString(_font, sub, new Vector2((w - ss.X) / 2, h / 2 + 20), Color.White);
            _spriteBatch.DrawString(_font, $"Reached Level {_player.Stats.Level}",
                new Vector2((w - _font.MeasureString($"Reached Level {_player.Stats.Level}").X) / 2, h / 2 + 50),
                Color.LightGray);

            _spriteBatch.End();
        }

        private void DrawVictory()
        {
            int w = GraphicsDevice.Viewport.Width, h = GraphicsDevice.Viewport.Height;
            _spriteBatch.Begin(SpriteSortMode.Deferred, BlendState.AlphaBlend);

            var pixel = new Texture2D(GraphicsDevice, 1, 1);
            pixel.SetData(new[] { Color.White });
            _spriteBatch.Draw(pixel, new Rectangle(0, 0, w, h), new Color(0, 0, 20, 200));

            string msg = "VICTORY!";
            string sub1 = "The Crystal Dragon has been defeated!";
            string sub2 = $"Level {_player.Stats.Level} | Gold: {_player.Gold}";
            string sub3 = "Press Enter to return to menu";

            float t = (float)(DateTime.Now.Millisecond / 1000.0);
            var titleColor = Color.Lerp(Color.Gold, new Color(100, 200, 255), MathF.Sin(t * 4f) * 0.5f + 0.5f);

            var ms = _bigFont.MeasureString(msg);
            _spriteBatch.DrawString(_bigFont, msg, new Vector2((w - ms.X) / 2, h / 2 - 100), titleColor);

            foreach (var (s, offset, col) in new[] {
                (sub1, 0, Color.White),
                (sub2, 28, Color.Gold),
                (sub3, 70, new Color(200,200,200))
            })
            {
                var ss = _font.MeasureString(s);
                _spriteBatch.DrawString(_font, s, new Vector2((w - ss.X) / 2, h / 2 + offset), col);
            }

            _spriteBatch.End();
        }

        private void AutoSave()
        {
            SaveSystem.Save(new SaveData
            {
                Level = _player.Stats.Level,
                Experience = _player.Stats.Experience,
                Health = _player.Stats.CurrentHealth,
                Gold = _player.Gold,
                PlayerX = _player.Position.X,
                PlayerZ = _player.Position.Z
            });
        }

        private SpriteFont CreateDefaultFont()
        {
            // This is a minimal fallback. In practice, the Content Pipeline provides fonts.
            // We cannot truly create a SpriteFont at runtime without Content Pipeline,
            // so this will gracefully fail and the game will use a null font guard.
            throw new Exception("Font content not found. Please build Content with MonoGame Pipeline.");
        }
    }

    // Helper struct to avoid warning
    internal ref struct Velocity
    {
        public Vector3 Value;
    }
}
