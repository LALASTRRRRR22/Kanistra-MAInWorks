using System;
using System.IO;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace AetherChronicles.Data
{
    public class SaveData
    {
        public int Level { get; set; }
        public int Experience { get; set; }
        public float Health { get; set; }
        public int Gold { get; set; }
        public float PlayerX { get; set; }
        public float PlayerZ { get; set; }
        public int GoblinsKilled { get; set; }
        public int OrcsKilled { get; set; }
        public bool DragonDefeated { get; set; }
        public DateTime SaveTime { get; set; }
    }

    public static class SaveSystem
    {
        private static readonly string SavePath =
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                "AetherChronicles", "save.json");

        public static void Save(SaveData data)
        {
            try
            {
                data.SaveTime = DateTime.Now;
                Directory.CreateDirectory(Path.GetDirectoryName(SavePath)!);
                File.WriteAllText(SavePath, JsonSerializer.Serialize(data,
                    new JsonSerializerOptions { WriteIndented = true }));
            }
            catch { }
        }

        public static SaveData? Load()
        {
            try
            {
                if (!File.Exists(SavePath)) return null;
                return JsonSerializer.Deserialize<SaveData>(File.ReadAllText(SavePath));
            }
            catch { return null; }
        }

        public static bool HasSave() => File.Exists(SavePath);
    }
}
