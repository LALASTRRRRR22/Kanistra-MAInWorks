using AetherChronicles.Data;
using Microsoft.Xna.Framework;
using System;
using System.Collections.Generic;

namespace AetherChronicles.Entities
{
    public enum DragonPhase { Grounded, Flying, Enraged }

    public class DragonBoss : Enemy
    {
        public DragonPhase Phase { get; private set; } = DragonPhase.Grounded;
        public List<MagicProjectile> BreathProjectiles { get; } = new();
        public float BreathTimer { get; private set; }
        public bool IsBreathing => BreathTimer > 0;

        private float _phaseTimer;
        private float _swoopTimer;
        private float _wingFlapAngle;
        public float WingFlapAngle => _wingFlapAngle;

        public DragonBoss()
        {
            Type = EntityType.DragonBoss;
            Stats = new CharacterStats
            {
                MaxHealth = 800, CurrentHealth = 800,
                BaseAttack = 40, BaseDefense = 20,
                MoveSpeed = 4f, AttackRange = 6f, AttackCooldown = 2.5f
            };
            AggroRange = 30f;
            AttackRangeThreshold = 6f;
            ExperienceReward = 2000;
            GoldReward = 500;
        }

        protected override void UpdateAI(float dt)
        {
            _wingFlapAngle += dt * 3f;

            foreach (var p in BreathProjectiles) p.Update(dt);
            BreathProjectiles.RemoveAll(p => !p.Active);

            if (BreathTimer > 0) BreathTimer -= dt;
            _phaseTimer -= dt;

            if (!IsAlive) return;

            // Phase transitions
            float healthPct = Stats.HealthPercent;
            if (healthPct < 0.5f && Phase == DragonPhase.Grounded)
            {
                Phase = DragonPhase.Flying;
                _phaseTimer = 8f;
            }
            if (healthPct < 0.25f && Phase != DragonPhase.Enraged)
            {
                Phase = DragonPhase.Enraged;
                Stats.MoveSpeed = 6f;
                Stats.BaseAttack = 60;
            }

            if (Target == null || !Target.IsAlive) return;

            float dist = Vector3.Distance(Position, Target.Position);

            switch (Phase)
            {
                case DragonPhase.Grounded:
                    UpdateGrounded(dt, dist);
                    break;
                case DragonPhase.Flying:
                    UpdateFlying(dt, dist);
                    break;
                case DragonPhase.Enraged:
                    UpdateEnraged(dt, dist);
                    break;
            }
        }

        private void UpdateGrounded(float dt, float dist)
        {
            if (dist <= AttackRangeThreshold)
            {
                State = EnemyState.Attack;
                var dir = Target!.Position - Position;
                if (dir.LengthSquared() > 0.01f)
                    Rotation = MathF.Atan2(dir.X, dir.Z);

                if (AttackTimer <= 0)
                {
                    // Tail swipe or bite
                    TryAttack(Target!);
                }
            }
            else if (dist < 12f && AttackTimer <= 0)
            {
                // Breath attack
                FireBreath();
            }
            else
            {
                State = EnemyState.Chase;
                MoveToward(Target!.Position, Stats.MoveSpeed, dt);
            }
        }

        private void UpdateFlying(float dt, float dist)
        {
            _swoopTimer -= dt;
            if (_swoopTimer <= 0)
            {
                _swoopTimer = (float)(Rng.NextDouble() * 3 + 2);
                // Swoop dive + breath
                FireBreath();
            }

            if (dist < 8f)
            {
                TryAttack(Target!);
            }
            else
            {
                MoveToward(Target!.Position, Stats.MoveSpeed * 1.3f, dt);
            }

            if (_phaseTimer <= 0) Phase = DragonPhase.Grounded;
        }

        private void UpdateEnraged(float dt, float dist)
        {
            // Relentless attack
            MoveToward(Target!.Position, Stats.MoveSpeed, dt);

            if (dist <= AttackRangeThreshold * 1.5f)
                TryAttack(Target!);

            if (AttackTimer <= 0 && dist < 15f)
                FireBreath();
        }

        private void FireBreath()
        {
            if (Target == null || BreathTimer > 0) return;
            BreathTimer = 1.5f;
            AttackTimer = 3f;
            IsAttacking = true;
            AttackAnimTimer = 1.5f;

            // Spread of projectiles
            var baseDir = Vector3.Normalize(Target.Position + Vector3.Up - (Position + Vector3.Up * 4f));
            for (int i = -2; i <= 2; i++)
            {
                float angle = i * 0.15f;
                var rotY = Matrix.CreateRotationY(angle);
                var dir = Vector3.Transform(baseDir, rotY);
                BreathProjectiles.Add(new MagicProjectile
                {
                    Position = Position + Vector3.Up * 4f,
                    Direction = dir,
                    Speed = 12f,
                    Damage = Stats.TotalAttack / 2,
                    Life = 2.5f
                });
            }
        }

        public void SetSpawnPoint(Vector3 pos) { SpawnPoint = pos; }
    }
}
