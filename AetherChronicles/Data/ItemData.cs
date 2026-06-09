using Microsoft.Xna.Framework;
using System.Collections.Generic;

namespace AetherChronicles.Data
{
    public enum ItemType
    {
        Weapon, Armor, Potion, Quest, Treasure
    }

    public enum Rarity
    {
        Common, Uncommon, Rare, Epic, Legendary
    }

    public class ItemData
    {
        public int Id { get; set; }
        public string Name { get; set; } = "";
        public string Description { get; set; } = "";
        public ItemType Type { get; set; }
        public Rarity Rarity { get; set; }
        public int Value { get; set; }
        public int AttackBonus { get; set; }
        public int DefenseBonus { get; set; }
        public int HealAmount { get; set; }
        public Color Color { get; set; } = Color.White;
        public int Quantity { get; set; } = 1;

        public static Color GetRarityColor(Rarity rarity) => rarity switch
        {
            Rarity.Common => Color.White,
            Rarity.Uncommon => Color.LimeGreen,
            Rarity.Rare => Color.CornflowerBlue,
            Rarity.Epic => new Color(160, 60, 200),
            Rarity.Legendary => new Color(255, 165, 0),
            _ => Color.White
        };
    }

    public static class ItemDatabase
    {
        public static readonly List<ItemData> All = new()
        {
            new() { Id=1, Name="Iron Sword", Description="A sturdy iron sword", Type=ItemType.Weapon, Rarity=Rarity.Common, AttackBonus=5, Value=50, Color=Color.LightGray },
            new() { Id=2, Name="Steel Blade", Description="Forged in ancient fires", Type=ItemType.Weapon, Rarity=Rarity.Uncommon, AttackBonus=12, Value=200, Color=Color.CornflowerBlue },
            new() { Id=3, Name="Aetherblade", Description="Infused with arcane energy", Type=ItemType.Weapon, Rarity=Rarity.Legendary, AttackBonus=35, Value=5000, Color=new Color(180,100,255) },
            new() { Id=4, Name="Leather Armor", Description="Basic leather protection", Type=ItemType.Armor, Rarity=Rarity.Common, DefenseBonus=5, Value=40, Color=new Color(160,82,45) },
            new() { Id=5, Name="Chain Mail", Description="Interlocked steel rings", Type=ItemType.Armor, Rarity=Rarity.Uncommon, DefenseBonus=15, Value=300, Color=Color.LightGray },
            new() { Id=6, Name="Dragon Scale Armor", Description="Scales of the ancient dragon", Type=ItemType.Armor, Rarity=Rarity.Legendary, DefenseBonus=50, Value=8000, Color=Color.Gold },
            new() { Id=7, Name="Health Potion", Description="Restores 50 health", Type=ItemType.Potion, Rarity=Rarity.Common, HealAmount=50, Value=25, Color=Color.Red },
            new() { Id=8, Name="Greater Elixir", Description="Restores 200 health", Type=ItemType.Potion, Rarity=Rarity.Rare, HealAmount=200, Value=150, Color=new Color(255,50,50) },
            new() { Id=9, Name="Crystal Shard", Description="Part of the dragon's heart", Type=ItemType.Quest, Rarity=Rarity.Epic, Value=0, Color=new Color(100,200,255) },
            new() { Id=10, Name="Gold Coin", Description="The currency of the realm", Type=ItemType.Treasure, Rarity=Rarity.Common, Value=1, Color=Color.Gold },
        };

        public static ItemData? GetById(int id) => All.Find(i => i.Id == id);
    }
}
