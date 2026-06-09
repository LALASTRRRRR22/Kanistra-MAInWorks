using AetherChronicles.Entities;
using AetherChronicles.Models;
using AetherChronicles.Rendering;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using System;
using System.Collections.Generic;

namespace AetherChronicles.World
{
    public class WorldObject
    {
        public Vector3 Position { get; set; }
        public float Rotation { get; set; }
        public float Scale { get; set; } = 1f;
        public GameModel Model { get; set; } = null!;
        public BoundingSphere? Collision { get; set; }
        public bool BlocksMovement { get; set; } = true;
    }

    public class GameWorld
    {
        private readonly GraphicsDevice _gd;
        private readonly Random _rng;

        public Terrain Terrain { get; private set; }
        public List<WorldObject> Objects { get; } = new();
        public List<Entity> Enemies { get; } = new();
        public DragonBoss? Boss { get; private set; }

        private GameModel _treeModel = null!;
        private GameModel _rockModel = null!;
        private GameModel _towerModel = null!;
        private GameModel _goblinModel = null!;
        private GameModel _orcModel = null!;
        private GameModel _mageModel = null!;
        private GameModel _dragonModel = null!;

        public float DayTime { get; private set; } = 0.5f; // 0=midnight, 0.5=noon
        public Color SkyColor { get; private set; } = Color.SkyBlue;
        public Color FogColor { get; private set; } = Color.SkyBlue;
        public float FogStart { get; private set; } = 80f;
        public float FogEnd { get; private set; } = 150f;

        public GameWorld(GraphicsDevice gd, int seed = 42)
        {
            _gd = gd;
            _rng = new Random(seed);
            Terrain = new Terrain(gd, seed);
        }

        public void LoadModels()
        {
            _treeModel = ModelFactory.CreateTree(_gd);
            _rockModel = ModelFactory.CreateRock(_gd);
            _towerModel = ModelFactory.CreateTower(_gd);
            _goblinModel = ModelFactory.CreateGoblin(_gd);
            _orcModel = ModelFactory.CreateOrcWarrior(_gd);
            _mageModel = ModelFactory.CreateDarkMage(_gd);
            _dragonModel = ModelFactory.CreateCrystalDragon(_gd);
        }

        public void Generate()
        {
            Objects.Clear();
            Enemies.Clear();

            // Scatter trees
            for (int i = 0; i < 80; i++)
            {
                var pos = RandomPos(60f);
                Objects.Add(new WorldObject
                {
                    Position = pos, Rotation = (float)(_rng.NextDouble() * MathF.PI * 2),
                    Scale = (float)(_rng.NextDouble() * 0.5f + 0.8f),
                    Model = _treeModel,
                    Collision = new BoundingSphere(pos + Vector3.Up, 0.6f)
                });
            }

            // Rocks
            for (int i = 0; i < 40; i++)
            {
                var pos = RandomPos(55f);
                Objects.Add(new WorldObject
                {
                    Position = pos, Rotation = (float)(_rng.NextDouble() * MathF.PI * 2),
                    Scale = (float)(_rng.NextDouble() * 0.6f + 0.7f),
                    Model = _rockModel,
                    Collision = new BoundingSphere(pos + Vector3.Up * 0.5f, 0.8f)
                });
            }

            // Towers / ruins
            for (int i = 0; i < 5; i++)
            {
                var pos = RandomPos(45f);
                Objects.Add(new WorldObject
                {
                    Position = pos, Rotation = (float)(_rng.NextDouble() * MathF.PI * 2),
                    Model = _towerModel,
                    Collision = new BoundingSphere(pos + Vector3.Up * 4f, 2f)
                });
            }

            // Spawn goblins (12)
            for (int i = 0; i < 12; i++)
            {
                var pos = RandomPos(40f);
                var goblin = new GoblinEnemy { Position = pos, Model = _goblinModel };
                goblin.SetSpawnPoint(pos);
                Enemies.Add(goblin);
            }

            // Spawn orcs (6)
            for (int i = 0; i < 6; i++)
            {
                var pos = RandomPos(50f);
                var orc = new OrcWarrior { Position = pos, Model = _orcModel };
                orc.SetSpawnPoint(pos);
                Enemies.Add(orc);
            }

            // Spawn dark mages (4)
            for (int i = 0; i < 4; i++)
            {
                var pos = RandomPos(50f);
                var mage = new DarkMageEnemy { Position = pos, Model = _mageModel };
                mage.SetSpawnPoint(pos);
                Enemies.Add(mage);
            }

            // Boss at center/back of map
            var bossPos = new Vector3(0, 0, -35f);
            Boss = new DragonBoss { Position = bossPos, Model = _dragonModel };
            Boss.SetSpawnPoint(bossPos);
        }

        public void Update(GameTime gameTime, Entity player)
        {
            float dt = (float)gameTime.ElapsedGameTime.TotalSeconds;

            // Day/night cycle (full day = 10 minutes)
            DayTime = (DayTime + dt / 600f) % 1f;
            UpdateSkyColors();

            // Update all enemies
            foreach (var enemy in Enemies)
            {
                if (!enemy.IsActive) continue;
                if (enemy is GoblinEnemy g) g.SetTarget(player);
                else if (enemy is OrcWarrior o) o.SetTarget(player);
                else if (enemy is DarkMageEnemy m) m.SetTarget(player);
                enemy.Update(gameTime);
            }

            Boss?.SetTarget(player);
            Boss?.Update(gameTime);
        }

        private void UpdateSkyColors()
        {
            // Dawn 0.25, Noon 0.5, Dusk 0.75, Night 0.0/1.0
            if (DayTime < 0.25f) // Night→Dawn
            {
                float t = DayTime / 0.25f;
                SkyColor = Color.Lerp(new Color(5, 5, 20), new Color(255, 150, 80), t);
                FogColor = Color.Lerp(new Color(10, 10, 30), new Color(200, 120, 60), t);
            }
            else if (DayTime < 0.5f) // Dawn→Noon
            {
                float t = (DayTime - 0.25f) / 0.25f;
                SkyColor = Color.Lerp(new Color(255, 150, 80), Color.SkyBlue, t);
                FogColor = Color.Lerp(new Color(200, 120, 60), new Color(180, 210, 230), t);
            }
            else if (DayTime < 0.75f) // Noon→Dusk
            {
                float t = (DayTime - 0.5f) / 0.25f;
                SkyColor = Color.Lerp(Color.SkyBlue, new Color(255, 100, 50), t);
                FogColor = Color.Lerp(new Color(180, 210, 230), new Color(200, 80, 40), t);
            }
            else // Dusk→Night
            {
                float t = (DayTime - 0.75f) / 0.25f;
                SkyColor = Color.Lerp(new Color(255, 100, 50), new Color(5, 5, 20), t);
                FogColor = Color.Lerp(new Color(200, 80, 40), new Color(10, 10, 30), t);
            }
        }

        public void DrawObjects(BasicEffect effect, Matrix view, Matrix projection)
        {
            foreach (var obj in Objects)
            {
                var world = Matrix.CreateScale(obj.Scale)
                    * Matrix.CreateRotationY(obj.Rotation)
                    * Matrix.CreateTranslation(obj.Position);
                obj.Model.Draw(effect, world, view, projection);
            }
        }

        public void DrawEnemies(BasicEffect effect, Matrix view, Matrix projection)
        {
            foreach (var e in Enemies)
            {
                if (e.IsActive && e.IsAlive)
                    e.Draw(effect, view, projection);
            }
        }

        public bool CheckCollision(Vector3 pos, float radius)
        {
            var sphere = new BoundingSphere(pos, radius);
            foreach (var obj in Objects)
            {
                if (!obj.BlocksMovement || obj.Collision == null) continue;
                if (sphere.Intersects(obj.Collision.Value)) return true;
            }
            return false;
        }

        private Vector3 RandomPos(float range)
        {
            float x = (float)(_rng.NextDouble() * range * 2 - range);
            float z = (float)(_rng.NextDouble() * range * 2 - range);
            return new Vector3(x, 0, z);
        }
    }
}
