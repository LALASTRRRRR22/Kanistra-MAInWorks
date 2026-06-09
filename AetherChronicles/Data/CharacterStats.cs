using System;

namespace AetherChronicles.Data
{
    public class CharacterStats
    {
        public int Level { get; set; } = 1;
        public int Experience { get; set; } = 0;
        public int ExperienceToNextLevel => Level * Level * 100;

        public int MaxHealth { get; set; } = 100;
        public float CurrentHealth { get; set; } = 100;

        public int BaseAttack { get; set; } = 10;
        public int BaseDefense { get; set; } = 5;
        public float MoveSpeed { get; set; } = 5f;
        public float AttackRange { get; set; } = 2.5f;
        public float AttackCooldown { get; set; } = 0.8f;

        public int WeaponAttack { get; set; } = 0;
        public int ArmorDefense { get; set; } = 0;

        public int TotalAttack => BaseAttack + WeaponAttack;
        public int TotalDefense => BaseDefense + ArmorDefense;

        public bool IsAlive => CurrentHealth > 0;

        public void TakeDamage(int damage)
        {
            int actualDamage = Math.Max(1, damage - TotalDefense);
            CurrentHealth = Math.Max(0, CurrentHealth - actualDamage);
        }

        public void Heal(int amount)
        {
            CurrentHealth = Math.Min(MaxHealth, CurrentHealth + amount);
        }

        public bool AddExperience(int xp)
        {
            Experience += xp;
            if (Experience >= ExperienceToNextLevel)
            {
                LevelUp();
                return true;
            }
            return false;
        }

        private void LevelUp()
        {
            Experience -= ExperienceToNextLevel;
            Level++;
            MaxHealth += 25;
            CurrentHealth = MaxHealth;
            BaseAttack += 3;
            BaseDefense += 2;
        }

        public float HealthPercent => CurrentHealth / MaxHealth;
        public float ExpPercent => (float)Experience / ExperienceToNextLevel;
    }
}
