using AetherChronicles.Rendering;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using System;

namespace AetherChronicles.Models
{
    public static class ModelFactory
    {
        public static GameModel CreateKnight(GraphicsDevice gd)
        {
            var model = new GameModel { Name = "Knight" };
            var bodyColor = new Color(100, 120, 160);
            var armorColor = new Color(180, 180, 200);
            var swordColor = new Color(200, 220, 240);
            var helmetColor = new Color(160, 160, 180);

            // Body (torso)
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateBox(gd, new Vector3(0.7f, 0.9f, 0.4f), bodyColor),
                LocalTransform = Matrix.CreateTranslation(0, 0.9f, 0)
            });
            // Head
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateBox(gd, new Vector3(0.45f, 0.45f, 0.45f), helmetColor),
                LocalTransform = Matrix.CreateTranslation(0, 1.75f, 0)
            });
            // Helmet crest
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateBox(gd, new Vector3(0.1f, 0.3f, 0.45f), new Color(200, 50, 50)),
                LocalTransform = Matrix.CreateTranslation(0, 2.1f, 0)
            });
            // Left arm
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateBox(gd, new Vector3(0.25f, 0.7f, 0.25f), armorColor),
                LocalTransform = Matrix.CreateTranslation(-0.5f, 0.85f, 0)
            });
            // Right arm
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateBox(gd, new Vector3(0.25f, 0.7f, 0.25f), armorColor),
                LocalTransform = Matrix.CreateTranslation(0.5f, 0.85f, 0)
            });
            // Left leg
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateBox(gd, new Vector3(0.28f, 0.8f, 0.28f), bodyColor),
                LocalTransform = Matrix.CreateTranslation(-0.2f, 0.1f, 0)
            });
            // Right leg
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateBox(gd, new Vector3(0.28f, 0.8f, 0.28f), bodyColor),
                LocalTransform = Matrix.CreateTranslation(0.2f, 0.1f, 0)
            });
            // Sword blade
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateBox(gd, new Vector3(0.08f, 1.2f, 0.06f), swordColor),
                LocalTransform = Matrix.CreateTranslation(0.85f, 1.2f, 0)
            });
            // Sword guard
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateBox(gd, new Vector3(0.4f, 0.08f, 0.1f), new Color(180, 140, 60)),
                LocalTransform = Matrix.CreateTranslation(0.85f, 0.75f, 0)
            });
            // Shield
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateBox(gd, new Vector3(0.1f, 0.6f, 0.5f), new Color(150, 30, 30)),
                LocalTransform = Matrix.CreateTranslation(-0.85f, 0.9f, 0)
            });

            model.BoundingSphere = new BoundingSphere(new Vector3(0, 1f, 0), 1.2f);
            return model;
        }

        public static GameModel CreateGoblin(GraphicsDevice gd)
        {
            var model = new GameModel { Name = "Goblin" };
            var skinColor = new Color(80, 140, 60);
            var clothColor = new Color(100, 70, 40);

            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateBox(gd, new Vector3(0.5f, 0.6f, 0.35f), skinColor),
                LocalTransform = Matrix.CreateTranslation(0, 0.65f, 0)
            });
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateBox(gd, new Vector3(0.4f, 0.4f, 0.4f), skinColor),
                LocalTransform = Matrix.CreateTranslation(0, 1.2f, 0)
            });
            // Big ears
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateBox(gd, new Vector3(0.15f, 0.25f, 0.08f), skinColor),
                LocalTransform = Matrix.CreateTranslation(-0.3f, 1.2f, 0)
            });
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateBox(gd, new Vector3(0.15f, 0.25f, 0.08f), skinColor),
                LocalTransform = Matrix.CreateTranslation(0.3f, 1.2f, 0)
            });
            // Arms
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateBox(gd, new Vector3(0.18f, 0.5f, 0.18f), skinColor),
                LocalTransform = Matrix.CreateTranslation(-0.38f, 0.6f, 0)
            });
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateBox(gd, new Vector3(0.18f, 0.5f, 0.18f), skinColor),
                LocalTransform = Matrix.CreateTranslation(0.38f, 0.6f, 0)
            });
            // Legs
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateBox(gd, new Vector3(0.2f, 0.55f, 0.2f), clothColor),
                LocalTransform = Matrix.CreateTranslation(-0.15f, 0.1f, 0)
            });
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateBox(gd, new Vector3(0.2f, 0.55f, 0.2f), clothColor),
                LocalTransform = Matrix.CreateTranslation(0.15f, 0.1f, 0)
            });
            // Dagger
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateBox(gd, new Vector3(0.06f, 0.5f, 0.05f), Color.LightGray),
                LocalTransform = Matrix.CreateTranslation(0.55f, 0.7f, 0)
            });

            model.BoundingSphere = new BoundingSphere(new Vector3(0, 0.7f, 0), 0.8f);
            return model;
        }

        public static GameModel CreateOrcWarrior(GraphicsDevice gd)
        {
            var model = new GameModel { Name = "OrcWarrior" };
            var skinColor = new Color(60, 100, 50);
            var armorColor = new Color(80, 80, 80);

            // Massive torso
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateBox(gd, new Vector3(1.1f, 1.2f, 0.7f), skinColor),
                LocalTransform = Matrix.CreateTranslation(0, 1.0f, 0)
            });
            // Head
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateBox(gd, new Vector3(0.7f, 0.7f, 0.65f), skinColor),
                LocalTransform = Matrix.CreateTranslation(0, 2.0f, 0)
            });
            // Tusks
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateBox(gd, new Vector3(0.08f, 0.25f, 0.06f), Color.Ivory),
                LocalTransform = Matrix.CreateTranslation(-0.2f, 1.75f, 0.3f)
            });
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateBox(gd, new Vector3(0.08f, 0.25f, 0.06f), Color.Ivory),
                LocalTransform = Matrix.CreateTranslation(0.2f, 1.75f, 0.3f)
            });
            // Armor chest plate
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateBox(gd, new Vector3(1.0f, 0.8f, 0.2f), armorColor),
                LocalTransform = Matrix.CreateTranslation(0, 1.1f, 0.35f)
            });
            // Arms
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateBox(gd, new Vector3(0.4f, 1.0f, 0.4f), skinColor),
                LocalTransform = Matrix.CreateTranslation(-0.85f, 0.9f, 0)
            });
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateBox(gd, new Vector3(0.4f, 1.0f, 0.4f), skinColor),
                LocalTransform = Matrix.CreateTranslation(0.85f, 0.9f, 0)
            });
            // Legs
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateBox(gd, new Vector3(0.42f, 0.9f, 0.42f), armorColor),
                LocalTransform = Matrix.CreateTranslation(-0.3f, 0.05f, 0)
            });
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateBox(gd, new Vector3(0.42f, 0.9f, 0.42f), armorColor),
                LocalTransform = Matrix.CreateTranslation(0.3f, 0.05f, 0)
            });
            // Axe handle
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateCylinder(gd, 0.08f, 1.5f, 8, new Color(100, 60, 20)),
                LocalTransform = Matrix.CreateTranslation(1.4f, 1.2f, 0)
            });
            // Axe blade
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateBox(gd, new Vector3(0.5f, 0.6f, 0.1f), Color.LightGray),
                LocalTransform = Matrix.CreateTranslation(1.4f, 1.8f, 0)
            });

            model.BoundingSphere = new BoundingSphere(new Vector3(0, 1.2f, 0), 1.5f);
            return model;
        }

        public static GameModel CreateDarkMage(GraphicsDevice gd)
        {
            var model = new GameModel { Name = "DarkMage" };
            var robeColor = new Color(40, 20, 60);
            var skinColor = new Color(200, 180, 160);

            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateCylinder(gd, 0.35f, 1.2f, 10, robeColor),
                LocalTransform = Matrix.CreateTranslation(0, 0.6f, 0)
            });
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateBox(gd, new Vector3(0.4f, 0.4f, 0.4f), skinColor),
                LocalTransform = Matrix.CreateTranslation(0, 1.5f, 0)
            });
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateCone(gd, 0.3f, 0.6f, 10, robeColor),
                LocalTransform = Matrix.CreateTranslation(0, 1.7f, 0)
            });
            // Staff
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateCylinder(gd, 0.05f, 1.8f, 6, new Color(60, 40, 20)),
                LocalTransform = Matrix.CreateTranslation(0.6f, 0.9f, 0)
            });
            // Orb
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateSphere(gd, 0.18f, 12, new Color(120, 0, 200)),
                LocalTransform = Matrix.CreateTranslation(0.6f, 1.85f, 0)
            });

            model.BoundingSphere = new BoundingSphere(new Vector3(0, 0.9f, 0), 1.0f);
            return model;
        }

        public static GameModel CreateCrystalDragon(GraphicsDevice gd)
        {
            var model = new GameModel { Name = "CrystalDragon" };
            var crystalColor = new Color(100, 200, 255);
            var darkCrystal = new Color(50, 100, 200);
            var glowColor = new Color(200, 240, 255);

            // Body
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateBox(gd, new Vector3(3f, 2f, 6f), crystalColor),
                LocalTransform = Matrix.CreateTranslation(0, 2f, 0)
            });
            // Neck
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateCylinder(gd, 0.7f, 2.5f, 10, crystalColor),
                LocalTransform = Matrix.CreateRotationX(-0.5f) * Matrix.CreateTranslation(0, 3.5f, -2.5f)
            });
            // Head
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateBox(gd, new Vector3(1.5f, 1.2f, 2f), darkCrystal),
                LocalTransform = Matrix.CreateTranslation(0, 4.5f, -4f)
            });
            // Horns
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateCone(gd, 0.25f, 1.2f, 6, glowColor),
                LocalTransform = Matrix.CreateTranslation(-0.5f, 5.5f, -3.5f)
            });
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateCone(gd, 0.25f, 1.2f, 6, glowColor),
                LocalTransform = Matrix.CreateTranslation(0.5f, 5.5f, -3.5f)
            });
            // Wings (left)
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateBox(gd, new Vector3(4f, 0.15f, 3f), new Color(80, 160, 255)),
                LocalTransform = Matrix.CreateRotationZ(0.4f) * Matrix.CreateTranslation(-3.5f, 3.5f, 0.5f)
            });
            // Wings (right)
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateBox(gd, new Vector3(4f, 0.15f, 3f), new Color(80, 160, 255)),
                LocalTransform = Matrix.CreateRotationZ(-0.4f) * Matrix.CreateTranslation(3.5f, 3.5f, 0.5f)
            });
            // Tail
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateCylinder(gd, 0.5f, 4f, 8, darkCrystal),
                LocalTransform = Matrix.CreateRotationX(0.3f) * Matrix.CreateTranslation(0, 1.5f, 3.5f)
            });
            // Crystal spikes on back
            for (int i = 0; i < 5; i++)
            {
                model.Parts.Add(new ModelPart
                {
                    Mesh = MeshBuilder.CreateCone(gd, 0.2f, 1.0f, 6, glowColor),
                    LocalTransform = Matrix.CreateTranslation(-1f + i * 0.5f, 3.5f, -1f + i * 0.8f)
                });
            }
            // Legs
            for (int side = -1; side <= 1; side += 2)
            {
                model.Parts.Add(new ModelPart
                {
                    Mesh = MeshBuilder.CreateCylinder(gd, 0.45f, 1.5f, 8, crystalColor),
                    LocalTransform = Matrix.CreateTranslation(side * 1.8f, 0.75f, 1.5f)
                });
                model.Parts.Add(new ModelPart
                {
                    Mesh = MeshBuilder.CreateCylinder(gd, 0.45f, 1.5f, 8, crystalColor),
                    LocalTransform = Matrix.CreateTranslation(side * 1.8f, 0.75f, -1.5f)
                });
            }

            model.BoundingSphere = new BoundingSphere(new Vector3(0, 2f, 0), 6f);
            return model;
        }

        public static GameModel CreateTree(GraphicsDevice gd)
        {
            var model = new GameModel { Name = "Tree" };
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateCylinder(gd, 0.25f, 2.5f, 8, new Color(100, 60, 20)),
                LocalTransform = Matrix.CreateTranslation(0, 1.25f, 0)
            });
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateSphere(gd, 1.5f, 12, new Color(30, 100, 30)),
                LocalTransform = Matrix.CreateTranslation(0, 3.5f, 0)
            });
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateSphere(gd, 1.0f, 10, new Color(40, 120, 40)),
                LocalTransform = Matrix.CreateTranslation(0.8f, 4.5f, 0)
            });
            model.BoundingSphere = new BoundingSphere(new Vector3(0, 2f, 0), 2f);
            return model;
        }

        public static GameModel CreateRock(GraphicsDevice gd)
        {
            var model = new GameModel { Name = "Rock" };
            var grayColor = new Color(120, 115, 110);
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateBox(gd, new Vector3(1.2f, 0.8f, 1.0f), grayColor),
                LocalTransform = Matrix.CreateTranslation(0, 0.4f, 0)
            });
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateBox(gd, new Vector3(0.8f, 0.6f, 0.7f), new Color(140, 135, 130)),
                LocalTransform = Matrix.CreateRotationY(0.5f) * Matrix.CreateTranslation(0, 0.7f, 0)
            });
            model.BoundingSphere = new BoundingSphere(new Vector3(0, 0.5f, 0), 0.8f);
            return model;
        }

        public static GameModel CreateTower(GraphicsDevice gd)
        {
            var model = new GameModel { Name = "Tower" };
            var stoneColor = new Color(130, 120, 110);
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateCylinder(gd, 1.5f, 8f, 12, stoneColor),
                LocalTransform = Matrix.CreateTranslation(0, 4f, 0)
            });
            model.Parts.Add(new ModelPart
            {
                Mesh = MeshBuilder.CreateCone(gd, 1.8f, 2.5f, 12, new Color(100, 30, 30)),
                LocalTransform = Matrix.CreateTranslation(0, 8f, 0)
            });
            for (int i = 0; i < 8; i++)
            {
                float a = i * MathF.PI / 4;
                model.Parts.Add(new ModelPart
                {
                    Mesh = MeshBuilder.CreateBox(gd, new Vector3(0.4f, 0.6f, 0.4f), stoneColor),
                    LocalTransform = Matrix.CreateTranslation(
                        MathF.Cos(a) * 1.5f, 8.3f, MathF.Sin(a) * 1.5f)
                });
            }
            model.BoundingSphere = new BoundingSphere(new Vector3(0, 4f, 0), 4f);
            return model;
        }
    }
}
