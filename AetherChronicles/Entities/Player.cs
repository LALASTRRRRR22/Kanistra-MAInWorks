using AetherChronicles.Data;
using AetherChronicles.Engine;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Input;
using System;
using System.Collections.Generic;

namespace AetherChronicles.Entities
{
    public class Player : Entity
    {
        public List<ItemData> Inventory { get; } = new();
        public int Gold { get; set; } = 0;
        public int EquippedWeaponId { get; private set; } = 1;
        public int EquippedArmorId { get; private set; } = 4;

        public float InvincibilityTimer { get; private set; }
        public bool IsInvincible => InvincibilityTimer > 0;
        public float DodgeTimer { get; private set; }
        public bool IsDodging => DodgeTimer > 0;
        public bool IsRolling { get; private set; }

        private readonly InputManager _input;
        private float _dodgeCooldown;
        private Vector3 _dodgeDir;

        public event Action<int>? OnLevelUp;
        public event Action<string>? OnPickupItem;

        public Player(InputManager input)
        {
            Type = EntityType.Player;
            _input = input;
            Stats = new CharacterStats
            {
                MaxHealth = 150, CurrentHealth = 150,
                BaseAttack = 15, BaseDefense = 8,
                MoveSpeed = 5.5f, AttackRange = 2.5f, AttackCooldown = 0.6f
            };
        }

        public override void Update(GameTime gameTime)
        {
            float dt = (float)gameTime.ElapsedGameTime.TotalSeconds;

            if (InvincibilityTimer > 0) InvincibilityTimer -= dt;
            if (AttackTimer > 0) AttackTimer -= dt;
            if (_dodgeCooldown > 0) _dodgeCooldown -= dt;
            if (AttackAnimTimer > 0) AttackAnimTimer -= dt;
            else IsAttacking = false;

            if (IsDodging)
            {
                DodgeTimer -= dt;
                Position += _dodgeDir * 12f * dt;
                IsRolling = true;
            }
            else
            {
                IsRolling = false;
                Position += Velocity * dt;
            }

            // Stay on ground
            Position = new Vector3(Position.X, 0f, Position.Z);
        }

        public Vector3 GetMovementInput(float cameraYaw)
        {
            var move = Vector3.Zero;
            if (_input.IsDown(Keys.W)) move.Z -= 1;
            if (_input.IsDown(Keys.S)) move.Z += 1;
            if (_input.IsDown(Keys.A)) move.X -= 1;
            if (_input.IsDown(Keys.D)) move.X += 1;

            if (move.LengthSquared() > 0)
            {
                move = Vector3.Normalize(move);
                var rotMatrix = Matrix.CreateRotationY(cameraYaw);
                move = Vector3.Transform(move, rotMatrix);
                Rotation = MathF.Atan2(move.X, move.Z);
            }

            return move * Stats.MoveSpeed;
        }

        public bool TryAttack()
        {
            if (AttackTimer > 0) return false;
            AttackTimer = Stats.AttackCooldown;
            IsAttacking = true;
            AttackAnimTimer = 0.3f;
            return true;
        }

        public bool TryDodge(Vector3 direction)
        {
            if (_dodgeCooldown > 0 || IsDodging) return false;
            if (direction.LengthSquared() < 0.01f)
                direction = new Vector3(MathF.Sin(Rotation), 0, MathF.Cos(Rotation));
            _dodgeDir = Vector3.Normalize(direction);
            DodgeTimer = 0.3f;
            _dodgeCooldown = 1.5f;
            InvincibilityTimer = 0.4f;
            return true;
        }

        public void UsePotion()
        {
            var potion = Inventory.Find(i => i.Type == ItemType.Potion && i.Quantity > 0);
            if (potion == null) return;
            Stats.Heal(potion.HealAmount);
            potion.Quantity--;
            if (potion.Quantity <= 0) Inventory.Remove(potion);
        }

        public void AddItem(ItemData item)
        {
            var existing = Inventory.Find(i => i.Id == item.Id);
            if (existing != null)
                existing.Quantity += item.Quantity;
            else
                Inventory.Add(new ItemData
                {
                    Id = item.Id, Name = item.Name, Description = item.Description,
                    Type = item.Type, Rarity = item.Rarity, Value = item.Value,
                    AttackBonus = item.AttackBonus, DefenseBonus = item.DefenseBonus,
                    HealAmount = item.HealAmount, Color = item.Color, Quantity = item.Quantity
                });
            OnPickupItem?.Invoke(item.Name);
        }

        public void EquipWeapon(ItemData weapon)
        {
            if (weapon.Type != ItemType.Weapon) return;
            // Unequip old
            var old = ItemDatabase.GetById(EquippedWeaponId);
            if (old != null) Stats.WeaponAttack -= old.AttackBonus;
            EquippedWeaponId = weapon.Id;
            Stats.WeaponAttack += weapon.AttackBonus;
        }

        public void EquipArmor(ItemData armor)
        {
            if (armor.Type != ItemType.Armor) return;
            var old = ItemDatabase.GetById(EquippedArmorId);
            if (old != null) Stats.ArmorDefense -= old.DefenseBonus;
            EquippedArmorId = armor.Id;
            Stats.ArmorDefense += armor.DefenseBonus;
        }

        public bool GainExperience(int xp)
        {
            bool leveled = Stats.AddExperience(xp);
            if (leveled) OnLevelUp?.Invoke(Stats.Level);
            return leveled;
        }

        public override void TakeDamage(int damage)
        {
            if (IsInvincible || IsDodging) return;
            base.TakeDamage(damage);
            InvincibilityTimer = 0.5f;
        }
    }
}
