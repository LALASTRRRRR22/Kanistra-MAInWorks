using AetherChronicles.Data;
using AetherChronicles.Models;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;

namespace AetherChronicles.Entities
{
    public enum EntityType { Player, Goblin, OrcWarrior, DarkMage, DragonBoss, NPC, Decoration }

    public abstract class Entity
    {
        public EntityType Type { get; protected set; }
        public Vector3 Position { get; set; }
        public float Rotation { get; set; }
        public Vector3 Velocity { get; set; }
        public CharacterStats Stats { get; protected set; } = new();
        public GameModel? Model { get; set; }
        public bool IsAlive => Stats.IsAlive;
        public bool IsActive { get; set; } = true;
        public BoundingSphere CollisionBounds =>
            new(Position + Vector3.Up * 1f, 0.8f);

        public float AttackTimer { get; protected set; } = 0f;
        public bool IsAttacking { get; protected set; }
        public float AttackAnimTimer { get; protected set; }

        public abstract void Update(GameTime gameTime);

        public virtual void Draw(BasicEffect effect, Matrix view, Matrix projection)
        {
            if (Model == null || !IsActive) return;
            var world = Matrix.CreateRotationY(Rotation) * Matrix.CreateTranslation(Position);
            Model.Draw(effect, world, view, projection);
        }

        public virtual void TakeDamage(int damage)
        {
            Stats.TakeDamage(damage);
        }
    }
}
