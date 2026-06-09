using AetherChronicles.Data;
using AetherChronicles.Entities;
using AetherChronicles.Rendering;
using Microsoft.Xna.Framework;
using System;
using System.Collections.Generic;

namespace AetherChronicles.Systems
{
    public class CombatEvent
    {
        public string Message { get; set; } = "";
        public Vector3 Position { get; set; }
        public float Timer { get; set; } = 2f;
        public Color Color { get; set; } = Color.White;
    }

    public class CombatSystem
    {
        private readonly ParticleSystem _particles;
        private readonly Random _rng = new();

        public List<CombatEvent> Events { get; } = new();

        public CombatSystem(ParticleSystem particles)
        {
            _particles = particles;
        }

        public void Update(float dt)
        {
            Events.RemoveAll(e => { e.Timer -= dt; return e.Timer <= 0; });
        }

        public bool PlayerAttack(Player player, List<Entity> enemies)
        {
            if (!player.TryAttack()) return false;

            bool hitAny = false;
            foreach (var enemy in enemies)
            {
                if (!enemy.IsAlive || !enemy.IsActive) continue;
                float dist = Vector3.Distance(player.Position, enemy.Position);
                if (dist > player.Stats.AttackRange) continue;

                // Angle check - player faces enemy
                var toEnemy = enemy.Position - player.Position;
                toEnemy.Y = 0;
                if (toEnemy.LengthSquared() < 0.01f) continue;

                var forward = new Vector3(MathF.Sin(player.Rotation), 0, MathF.Cos(player.Rotation));
                float dot = Vector3.Dot(Vector3.Normalize(toEnemy), forward);
                if (dot < 0.1f) continue; // Must be roughly facing

                int damage = CalculateDamage(player.Stats.TotalAttack, enemy.Stats.TotalDefense);
                enemy.TakeDamage(damage);

                _particles.Emit(ParticleEffect.Hit, enemy.Position + Vector3.Up);
                if (!enemy.IsAlive)
                    _particles.Emit(ParticleEffect.Death, enemy.Position + Vector3.Up);

                AddEvent($"-{damage}", enemy.Position + Vector3.Up * 2f, new Color(255, 80, 80));
                hitAny = true;

                if (enemy is Enemy e) e.ApplyHitEffect();
            }

            return hitAny;
        }

        public void EnemyAttackPlayer(Enemy enemy, Player player)
        {
            if (!enemy.TryAttack(player)) return;

            float dist = Vector3.Distance(enemy.Position, player.Position);
            if (dist > enemy.Stats.AttackRange + 0.5f) return;

            int damage = CalculateDamage(enemy.Stats.TotalAttack, player.Stats.TotalDefense);
            player.TakeDamage(damage);

            if (!player.IsInvincible)
            {
                _particles.Emit(ParticleEffect.Blood, player.Position + Vector3.Up);
                AddEvent($"-{damage}", player.Position + Vector3.Up * 2.5f, Color.Red);
            }
        }

        public bool CheckProjectileHit(MagicProjectile proj, Player player)
        {
            if (!proj.Active) return false;
            float dist = Vector3.Distance(proj.Position, player.Position + Vector3.Up);
            if (dist > 0.8f) return false;

            proj.Active = false;
            player.TakeDamage(proj.Damage);
            _particles.Emit(ParticleEffect.Magic, proj.Position);
            AddEvent($"-{proj.Damage}", player.Position + Vector3.Up * 2.5f, new Color(150, 50, 255));
            return true;
        }

        public int ProcessEnemyDeath(Enemy enemy, Player player)
        {
            int xp = enemy.ExperienceReward;
            int gold = enemy.GoldReward;

            _particles.Emit(ParticleEffect.Explosion, enemy.Position + Vector3.Up);
            AddEvent($"+{xp} XP", enemy.Position + Vector3.Up * 2f, Color.Gold);
            AddEvent($"+{gold} G", enemy.Position + Vector3.Up * 2.5f, new Color(255, 215, 0));

            enemy.IsActive = false;
            player.Gold += gold;
            bool leveled = player.GainExperience(xp);
            if (leveled)
            {
                _particles.Emit(ParticleEffect.LevelUp, player.Position);
                AddEvent("LEVEL UP!", player.Position + Vector3.Up * 3f, Color.Gold);
            }

            return xp;
        }

        private int CalculateDamage(int attack, int defense)
        {
            int variance = _rng.Next(-3, 4);
            int rawDamage = attack - defense / 2 + variance;
            return Math.Max(1, rawDamage);
        }

        private void AddEvent(string msg, Vector3 pos, Color color)
        {
            Events.Add(new CombatEvent { Message = msg, Position = pos, Color = color });
        }
    }
}
