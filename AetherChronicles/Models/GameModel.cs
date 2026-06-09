using AetherChronicles.Rendering;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using System.Collections.Generic;

namespace AetherChronicles.Models
{
    public class ModelPart
    {
        public GameMesh Mesh { get; set; } = null!;
        public Matrix LocalTransform { get; set; } = Matrix.Identity;
        public Color Color { get; set; } = Color.White;
    }

    public class GameModel
    {
        public List<ModelPart> Parts { get; } = new();
        public string Name { get; set; } = "";
        public BoundingSphere BoundingSphere { get; set; }

        public void Draw(BasicEffect effect, Matrix world, Matrix view, Matrix projection)
        {
            effect.View = view;
            effect.Projection = projection;
            effect.LightingEnabled = true;
            effect.DirectionalLight0.Enabled = true;
            effect.DirectionalLight0.Direction = Vector3.Normalize(new Vector3(1, -2, 1));
            effect.DirectionalLight0.DiffuseColor = Vector3.One;
            effect.AmbientLightColor = new Vector3(0.3f, 0.3f, 0.4f);

            foreach (var part in Parts)
            {
                if (part.Mesh.VertexBuffer == null) continue;
                effect.World = part.LocalTransform * world;
                effect.DiffuseColor = part.Color.ToVector3();
                effect.VertexColorEnabled = false;

                effect.GraphicsDevice.SetVertexBuffer(part.Mesh.VertexBuffer);
                effect.GraphicsDevice.Indices = part.Mesh.IndexBuffer;

                foreach (var pass in effect.CurrentTechnique.Passes)
                {
                    pass.Apply();
                    effect.GraphicsDevice.DrawIndexedPrimitives(
                        PrimitiveType.TriangleList, 0, 0, part.Mesh.PrimitiveCount);
                }
            }
        }
    }
}
