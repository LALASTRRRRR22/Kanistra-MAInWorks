using AetherChronicles.Data;
using Microsoft.Xna.Framework;
using System;

namespace AetherChronicles.Entities
{
    public class OrcWarrior : Enemy
    {
        private float _chargeTimer;
        private bool _isCharging;
        private Vector3 _chargeDir;

        public OrcWarrior()
        {
            Type = EntityType.OrcWarrior;
            Stats = new CharacterStats
            {
                MaxHealth = 120, CurrentHealth = 120,
                BaseAttack = 22, BaseDefense = 10,
                MoveSpeed = 3f, AttackRange = 2.5f, AttackCooldown = 1.8f
            };
            AggroRange = 14f;
            AttackRangeThreshold = 2.5f;
            ExperienceReward = 100;
            GoldReward = Rng.Next(15, 35);
        }

        protected override void UpdateAI(float dt)
        {
            if (Target == null || !Target.IsAlive)
            {
                PatrolSlow(dt);
                return;
            }

            float dist = Vector3.Distance(Position, Target.Position);

            if (_isCharging)
            {
                _chargeTimer -= dt;
                Position += _chargeDir * 10f * dt;
                Position = new Vector3(Position.X, 0, Position.Z);
                if (_chargeTimer <= 0) _isCharging = false;
                return;
            }

            if (dist > AggroRange)
            {
                PatrolSlow(dt);
                return;
            }

            if (dist <= AttackRangeThreshold)
            {
                State = EnemyState.Attack;
                var dir = Target.Position - Position;
                if (dir.LengthSquared() > 0.01f)
                    Rotation = MathF.Atan2(dir.X, dir.Z);
            }
            else if (dist < 8f && _chargeTimer <= 0 && AttackTimer <= 0)
            {
                // Charge attack!
                _isCharging = true;
                _chargeTimer = 0.4f;
                _chargeDir = Vector3.Normalize(Target.Position - Position);
                _chargeDir.Y = 0;
            }
            else
            {
                State = EnemyState.Chase;
                MoveToward(Target.Position, Stats.MoveSpeed, dt);
            }
        }

        private void PatrolSlow(float dt)
        {
            PatrolTimer -= dt;
            if (PatrolTimer <= 0)
            {
                PatrolTimer = (float)(Rng.NextDouble() * 4 + 3);
                PatrolTarget = SpawnPoint + new Vector3(
                    (float)(Rng.NextDouble() * 5 - 2.5f), 0,
                    (float)(Rng.NextDouble() * 5 - 2.5f));
            }
            MoveToward(PatrolTarget, Stats.MoveSpeed * 0.4f, dt);
        }

        public void SetSpawnPoint(Vector3 pos) { SpawnPoint = pos; PatrolTarget = pos; }
    }
}
