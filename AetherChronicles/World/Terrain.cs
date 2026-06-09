using AetherChronicles.Rendering;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using System;

namespace AetherChronicles.World
{
    public class Terrain
    {
        private VertexBuffer? _vertexBuffer;
        private IndexBuffer? _indexBuffer;
        private int _primitiveCount;
        private readonly int _size;
        private readonly float[,] _heights;
        private readonly Random _rng;

        public Terrain(GraphicsDevice gd, int seed = 42)
        {
            _rng = new Random(seed);
            _size = 128;
            _heights = new float[_size + 1, _size + 1];
            GenerateHeights();
            BuildMesh(gd);
        }

        private void GenerateHeights()
        {
            // Simple Perlin-like noise using multiple sine waves
            for (int z = 0; z <= _size; z++)
            {
                for (int x = 0; x <= _size; x++)
                {
                    float wx = (x - _size / 2f) * 2.5f;
                    float wz = (z - _size / 2f) * 2.5f;

                    float h = 0;
                    h += MathF.Sin(wx * 0.02f + 1.3f) * MathF.Cos(wz * 0.015f) * 4f;
                    h += MathF.Sin(wx * 0.05f + 0.7f) * MathF.Cos(wz * 0.04f + 0.5f) * 2f;
                    h += MathF.Sin(wx * 0.1f + 2.1f) * MathF.Cos(wz * 0.09f + 1.1f) * 1f;

                    // Flatten center area (player start zone)
                    float distFromCenter = MathF.Sqrt(wx * wx + wz * wz);
                    float flatFactor = MathF.Max(0, 1f - distFromCenter / 30f);
                    h *= (1f - flatFactor);

                    _heights[x, z] = h;
                }
            }
        }

        private void BuildMesh(GraphicsDevice gd)
        {
            var vertices = new VertexPositionColorNormal[(_size + 1) * (_size + 1)];

            for (int z = 0; z <= _size; z++)
            {
                for (int x = 0; x <= _size; x++)
                {
                    float wx = (x - _size / 2f) * 2.5f;
                    float wz = (z - _size / 2f) * 2.5f;
                    float h = _heights[x, z];

                    // Color based on height
                    Color color;
                    if (h < -1f)       color = new Color(60, 80, 140);    // water
                    else if (h < 0.5f) color = new Color(80, 140, 60);    // grass
                    else if (h < 2f)   color = new Color(100, 160, 70);   // hills
                    else if (h < 4f)   color = new Color(140, 120, 90);   // mountain
                    else               color = new Color(220, 220, 230);  // snow

                    var normal = ComputeNormal(x, z);
                    vertices[z * (_size + 1) + x] = new VertexPositionColorNormal(
                        new Vector3(wx, h, wz), color, normal);
                }
            }

            var indices = new int[_size * _size * 6];
            int idx = 0;
            for (int z = 0; z < _size; z++)
            {
                for (int x = 0; x < _size; x++)
                {
                    int tl = z * (_size + 1) + x;
                    int tr = tl + 1;
                    int bl = (z + 1) * (_size + 1) + x;
                    int br = bl + 1;
                    indices[idx++] = tl; indices[idx++] = bl; indices[idx++] = tr;
                    indices[idx++] = tr; indices[idx++] = bl; indices[idx++] = br;
                }
            }

            _vertexBuffer = new VertexBuffer(gd, VertexPositionColorNormal.VertexDeclaration,
                vertices.Length, BufferUsage.WriteOnly);
            _vertexBuffer.SetData(vertices);

            _indexBuffer = new IndexBuffer(gd, IndexElementSize.ThirtyTwoBits,
                indices.Length, BufferUsage.WriteOnly);
            _indexBuffer.SetData(indices);

            _primitiveCount = indices.Length / 3;
        }

        private Vector3 ComputeNormal(int x, int z)
        {
            float l = GetH(x - 1, z), r = GetH(x + 1, z);
            float d = GetH(x, z - 1), u = GetH(x, z + 1);
            return Vector3.Normalize(new Vector3(l - r, 2f, d - u));
        }

        private float GetH(int x, int z)
        {
            x = Math.Clamp(x, 0, _size);
            z = Math.Clamp(z, 0, _size);
            return _heights[x, z];
        }

        public float GetHeightAt(float worldX, float worldZ)
        {
            float gx = worldX / 2.5f + _size / 2f;
            float gz = worldZ / 2.5f + _size / 2f;
            int ix = (int)gx, iz = (int)gz;
            ix = Math.Clamp(ix, 0, _size - 1);
            iz = Math.Clamp(iz, 0, _size - 1);

            float fx = gx - ix, fz = gz - iz;
            float h00 = GetH(ix, iz), h10 = GetH(ix + 1, iz);
            float h01 = GetH(ix, iz + 1), h11 = GetH(ix + 1, iz + 1);

            return h00 * (1 - fx) * (1 - fz)
                 + h10 * fx * (1 - fz)
                 + h01 * (1 - fx) * fz
                 + h11 * fx * fz;
        }

        public void Draw(BasicEffect effect, Matrix view, Matrix projection)
        {
            if (_vertexBuffer == null || _indexBuffer == null) return;

            effect.World = Matrix.Identity;
            effect.View = view;
            effect.Projection = projection;
            effect.LightingEnabled = true;
            effect.DirectionalLight0.Enabled = true;
            effect.DirectionalLight0.Direction = Vector3.Normalize(new Vector3(0.5f, -1f, 0.3f));
            effect.DirectionalLight0.DiffuseColor = new Vector3(0.9f, 0.85f, 0.7f);
            effect.AmbientLightColor = new Vector3(0.3f, 0.35f, 0.4f);
            effect.VertexColorEnabled = true;

            effect.GraphicsDevice.SetVertexBuffer(_vertexBuffer);
            effect.GraphicsDevice.Indices = _indexBuffer;

            foreach (var pass in effect.CurrentTechnique.Passes)
            {
                pass.Apply();
                effect.GraphicsDevice.DrawIndexedPrimitives(
                    PrimitiveType.TriangleList, 0, 0, _primitiveCount);
            }
        }
    }
}
