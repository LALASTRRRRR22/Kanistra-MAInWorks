using AetherChronicles.Data;
using Microsoft.Xna.Framework;
using System;

namespace AetherChronicles.Entities
{
    public class GoblinEnemy : Enemy
    {
        public GoblinEnemy()
        {
            Type = EntityType.Goblin;
            Stats = new CharacterStats
            {
                MaxHealth = 40, CurrentHealth = 40,
                BaseAttack = 8, BaseDefense = 2,
                MoveSpeed = 4.5f, AttackRange = 1.5f, AttackCooldown = 1.0f
            };
            AggroRange = 12f;
            AttackRangeThreshold = 1.5f;
            ExperienceReward = 30;
            GoldReward = Rng.Next(3, 12);
        }

        protected override void UpdateAI(float dt)
        {
            if (Target == null || !Target.IsAlive)
            {
                Patrol(dt);
                return;
            }

            float dist = Vector3.Distance(Position, Target.Position);

            if (dist > AggroRange)
            {
                State = EnemyState.Patrol;
                Patrol(dt);
                return;
            }

            if (dist <= AttackRangeThreshold)
            {
                State = EnemyState.Attack;
                // Face the target
                var dir = Target.Position - Position;
                if (dir.LengthSquared() > 0.01f)
                    Rotation = MathF.Atan2(dir.X, dir.Z);
            }
            else
            {
                State = EnemyState.Chase;
                // Goblins are erratic — add a small random offset
                float jitter = MathF.Sin((float)Environment.TickCount * 0.01f) * 0.5f;
                var offset = new Vector3(jitter, 0, jitter * 0.5f);
                MoveToward(Target.Position + offset, Stats.MoveSpeed, dt);
            }
        }

        private void Patrol(float dt)
        {
            PatrolTimer -= dt;
            if (PatrolTimer <= 0)
            {
                PatrolTimer = (float)(Rng.NextDouble() * 3 + 2);
                PatrolTarget = SpawnPoint + new Vector3(
                    (float)(Rng.NextDouble() * 6 - 3), 0,
                    (float)(Rng.NextDouble() * 6 - 3));
            }
            MoveToward(PatrolTarget, Stats.MoveSpeed * 0.5f, dt);
        }

        public void SetSpawnPoint(Vector3 pos)
        {
            SpawnPoint = pos;
            PatrolTarget = pos;
        }
    }
}
