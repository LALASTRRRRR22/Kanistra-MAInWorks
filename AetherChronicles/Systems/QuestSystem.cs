using AetherChronicles.Data;
using AetherChronicles.Entities;
using System;
using System.Collections.Generic;
using System.Linq;

namespace AetherChronicles.Systems
{
    public class QuestSystem
    {
        public List<QuestData> Quests { get; }
        public event Action<QuestData>? OnQuestComplete;
        public event Action<QuestData>? OnQuestStarted;

        private int _goblinsKilled;
        private int _orcsKilled;

        private int _potionsCollected;

        public QuestSystem()
        {
            Quests = QuestDatabase.CreateDefaultQuests();
            // Auto-start first quest
            Quests[0].Status = QuestStatus.Active;
        }

        public void OnEnemyKilled(EntityType type)
        {
            switch (type)
            {
                case EntityType.Goblin:
                    _goblinsKilled++;
                    UpdateObjective(1, 0, _goblinsKilled);
                    TryStartQuest(2);
                    break;
                case EntityType.OrcWarrior:
                    _orcsKilled++;
                    UpdateObjective(2, 0, _orcsKilled);
                    TryStartQuest(3);
                    break;
                case EntityType.DragonBoss:
                    UpdateObjective(3, 0, 1);
                    break;
            }
        }

        public void OnItemPickup(ItemType type)
        {
            if (type == ItemType.Potion)
            {
                _potionsCollected++;
                UpdateObjective(4, 0, _potionsCollected);
                TryStartQuest(4);
            }
        }

        private void UpdateObjective(int questId, int objIndex, int value)
        {
            var quest = Quests.Find(q => q.Id == questId);
            if (quest == null || quest.Status != QuestStatus.Active) return;
            if (objIndex >= quest.Objectives.Count) return;

            quest.Objectives[objIndex].Current = Math.Min(value, quest.Objectives[objIndex].Required);

            if (quest.IsAllObjectivesComplete)
            {
                quest.Status = QuestStatus.Completed;
                OnQuestComplete?.Invoke(quest);
            }
        }

        private void TryStartQuest(int questId)
        {
            var quest = Quests.Find(q => q.Id == questId);
            if (quest != null && quest.Status == QuestStatus.NotStarted)
            {
                quest.Status = QuestStatus.Active;
                OnQuestStarted?.Invoke(quest);
            }
        }

        public IEnumerable<QuestData> ActiveQuests => Quests.Where(q => q.Status == QuestStatus.Active);
        public IEnumerable<QuestData> CompletedQuests => Quests.Where(q => q.Status == QuestStatus.Completed);
    }
}
