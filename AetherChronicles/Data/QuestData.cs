using System.Collections.Generic;

namespace AetherChronicles.Data
{
    public enum QuestStatus { NotStarted, Active, Completed, Failed }

    public class QuestObjective
    {
        public string Description { get; set; } = "";
        public int Required { get; set; } = 1;
        public int Current { get; set; } = 0;
        public bool IsComplete => Current >= Required;
        public string Progress => $"{Current}/{Required}";
    }

    public class QuestData
    {
        public int Id { get; set; }
        public string Title { get; set; } = "";
        public string Description { get; set; } = "";
        public QuestStatus Status { get; set; } = QuestStatus.NotStarted;
        public List<QuestObjective> Objectives { get; set; } = new();
        public int RewardXP { get; set; }
        public int RewardGold { get; set; }
        public int? RewardItemId { get; set; }

        public bool IsAllObjectivesComplete => Objectives.TrueForAll(o => o.IsComplete);
    }

    public static class QuestDatabase
    {
        public static List<QuestData> CreateDefaultQuests() => new()
        {
            new QuestData
            {
                Id = 1,
                Title = "First Blood",
                Description = "Prove your worth by defeating the goblin scouts.",
                RewardXP = 150, RewardGold = 50,
                Objectives = new()
                {
                    new() { Description = "Defeat Goblin Scouts", Required = 5 }
                }
            },
            new QuestData
            {
                Id = 2,
                Title = "The Orc Threat",
                Description = "The Orc Warriors are raiding the nearby villages. Stop them!",
                RewardXP = 400, RewardGold = 200,
                Objectives = new()
                {
                    new() { Description = "Defeat Orc Warriors", Required = 3 }
                }
            },
            new QuestData
            {
                Id = 3,
                Title = "Crystal Dragon",
                Description = "The Crystal Dragon threatens the realm. Only you can stop it.",
                RewardXP = 2000, RewardGold = 1000, RewardItemId = 9,
                Objectives = new()
                {
                    new() { Description = "Slay the Crystal Dragon", Required = 1 }
                }
            },
            new QuestData
            {
                Id = 4,
                Title = "Potion Collector",
                Description = "Stock up on health potions for the journey ahead.",
                RewardXP = 100, RewardGold = 75,
                Objectives = new()
                {
                    new() { Description = "Collect Health Potions", Required = 3 }
                }
            }
        };
    }
}
