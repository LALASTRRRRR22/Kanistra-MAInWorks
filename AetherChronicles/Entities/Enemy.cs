using AetherChronicles.Data;
using Microsoft.Xna.Framework;
using System;

namespace AetherChronicles.Entities
{
    public enum EnemyState { Idle, Patrol, Chase, Attack, Hit, Death }

    public abstract class Enemy : Entity
    {
        public EnemyState State { get; protected set; } = EnemyState.Idle;
        public int ExperienceReward { get; protected set; }
        public int GoldReward { get; protected set; }
        public float AggroRange { get; protected set; } = 10f;
        public float AttackRangeThreshold { get; protected set; } = 2f;

        protected Vector3 PatrolTarget;
        protected Vector3 SpawnPoint;
        protected float PatrolTimer;
        protected float HitTimer;
        protected Entity? Target;

        protected readonly Random Rng = new();

        public override void Update(GameTime gameTime)
        {
            float dt = (float)gameTime.ElapsedGameTime.TotalSeconds;
            if (AttackTimer > 0) AttackTimer -= dt;
            if (HitTimer > 0) HitTimer -= dt;
            if (AttackAnimTimer > 0) { AttackAnimTimer -= dt; }
            else IsAttacking = false;

            if (!IsAlive)
            {
                State = EnemyState.Death;
                return;
            }

            UpdateAI(dt);
        }

        protected abstract void UpdateAI(float dt);

        public void SetTarget(Entity target) => Target = target;

        protected void MoveToward(Vector3 targetPos, float speed, float dt)
        {
            var diff = targetPos - Position;
            diff.Y = 0;
            if (diff.LengthSquared() > 0.01f)
            {
                var dir = Vector3.Normalize(diff);
                Position += dir * speed * dt;
                Position = new Vector3(Position.X, 0, Position.Z);
                Rotation = MathF.Atan2(dir.X, dir.Z);
            }
        }

        public bool TryAttack(Entity target)
        {
            if (AttackTimer > 0) return false;
            AttackTimer = Stats.AttackCooldown;
            IsAttacking = true;
            AttackAnimTimer = 0.4f;
            return true;
        }

        public void ApplyHitEffect()
        {
            HitTimer = 0.2f;
            State = EnemyState.Hit;
        }
    }
}
