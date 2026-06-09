using AetherChronicles.Data;
using Microsoft.Xna.Framework;
using System;

namespace AetherChronicles.Entities
{
    public class MagicProjectile
    {
        public Vector3 Position;
        public Vector3 Direction;
        public float Speed = 8f;
        public float Life = 3f;
        public bool Active = true;
        public int Damage = 15;

        public void Update(float dt)
        {
            if (!Active) return;
            Position += Direction * Speed * dt;
            Life -= dt;
            if (Life <= 0) Active = false;
        }
    }

    public class DarkMageEnemy : Enemy
    {
        public System.Collections.Generic.List<MagicProjectile> Projectiles { get; } = new();
        private float _castCooldown;

        public DarkMageEnemy()
        {
            Type = EntityType.DarkMage;
            Stats = new CharacterStats
            {
                MaxHealth = 70, CurrentHealth = 70,
                BaseAttack = 18, BaseDefense = 3,
                MoveSpeed = 2.5f, AttackRange = 10f, AttackCooldown = 2.0f
            };
            AggroRange = 16f;
            AttackRangeThreshold = 8f;
            ExperienceReward = 80;
            GoldReward = Rng.Next(10, 25);
        }

        protected override void UpdateAI(float dt)
        {
            _castCooldown -= dt;

            foreach (var proj in Projectiles)
                proj.Update(dt);
            Projectiles.RemoveAll(p => !p.Active);

            if (Target == null || !Target.IsAlive) return;

            float dist = Vector3.Distance(Position, Target.Position);
            if (dist > AggroRange) return;

            // Strafe
            State = EnemyState.Chase;
            float strafeAngle = (float)(Environment.TickCount * 0.001);
            var strafeOffset = new Vector3(MathF.Cos(strafeAngle) * 2f, 0, MathF.Sin(strafeAngle) * 2f);
            var keepDistance = Target.Position + strafeOffset;
            var keepDir = keepDistance - Position;
            keepDir.Y = 0;

            if (dist < 5f)
            {
                // Back away
                MoveToward(Position - Vector3.Normalize(Target.Position - Position) * 3f, Stats.MoveSpeed, dt);
            }
            else if (dist > 10f)
            {
                MoveToward(Target.Position, Stats.MoveSpeed, dt);
            }

            // Cast spell
            if (_castCooldown <= 0 && dist <= AttackRangeThreshold)
            {
                _castCooldown = Stats.AttackCooldown;
                ShootProjectile();
            }
        }

        private void ShootProjectile()
        {
            if (Target == null) return;
            var dir = Target.Position + Vector3.Up * 1f - (Position + Vector3.Up * 1.8f);
            if (dir.LengthSquared() < 0.01f) return;
            dir = Vector3.Normalize(dir);

            Projectiles.Add(new MagicProjectile
            {
                Position = Position + Vector3.Up * 1.8f,
                Direction = dir,
                Damage = Stats.TotalAttack
            });
            IsAttacking = true;
            AttackAnimTimer = 0.5f;
        }

        public void SetSpawnPoint(Vector3 pos) { SpawnPoint = pos; PatrolTarget = pos; }
    }
}
