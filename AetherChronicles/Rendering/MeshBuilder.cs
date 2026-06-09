using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using System;
using System.Collections.Generic;

namespace AetherChronicles.Rendering
{
    public class GameMesh
    {
        public VertexBuffer? VertexBuffer;
        public IndexBuffer? IndexBuffer;
        public int PrimitiveCount;
        public BoundingSphere BoundingSphere;
    }

    public static class MeshBuilder
    {
        public static GameMesh CreateBox(GraphicsDevice gd, Vector3 size, Color color)
        {
            float hx = size.X * 0.5f, hy = size.Y * 0.5f, hz = size.Z * 0.5f;

            var vertices = new VertexPositionColorNormal[]
            {
                // Front
                new(new(-hx,-hy, hz), color, Vector3.Forward),
                new(new( hx,-hy, hz), color, Vector3.Forward),
                new(new( hx, hy, hz), color, Vector3.Forward),
                new(new(-hx, hy, hz), color, Vector3.Forward),
                // Back
                new(new( hx,-hy,-hz), color, Vector3.Backward),
                new(new(-hx,-hy,-hz), color, Vector3.Backward),
                new(new(-hx, hy,-hz), color, Vector3.Backward),
                new(new( hx, hy,-hz), color, Vector3.Backward),
                // Left
                new(new(-hx,-hy,-hz), color, Vector3.Left),
                new(new(-hx,-hy, hz), color, Vector3.Left),
                new(new(-hx, hy, hz), color, Vector3.Left),
                new(new(-hx, hy,-hz), color, Vector3.Left),
                // Right
                new(new( hx,-hy, hz), color, Vector3.Right),
                new(new( hx,-hy,-hz), color, Vector3.Right),
                new(new( hx, hy,-hz), color, Vector3.Right),
                new(new( hx, hy, hz), color, Vector3.Right),
                // Top
                new(new(-hx, hy, hz), color, Vector3.Up),
                new(new( hx, hy, hz), color, Vector3.Up),
                new(new( hx, hy,-hz), color, Vector3.Up),
                new(new(-hx, hy,-hz), color, Vector3.Up),
                // Bottom
                new(new(-hx,-hy,-hz), color, Vector3.Down),
                new(new( hx,-hy,-hz), color, Vector3.Down),
                new(new( hx,-hy, hz), color, Vector3.Down),
                new(new(-hx,-hy, hz), color, Vector3.Down),
            };

            var indices = new List<short>();
            for (short i = 0; i < 6; i++)
            {
                short b = (short)(i * 4);
                indices.AddRange(new short[] { b, (short)(b+1), (short)(b+2), b, (short)(b+2), (short)(b+3) });
            }

            return CreateMesh(gd, vertices, indices.ToArray(), BoundingSphere.CreateFromPoints(ToV3(vertices)));
        }

        public static GameMesh CreateSphere(GraphicsDevice gd, float radius, int segments, Color color)
        {
            var verts = new List<VertexPositionColorNormal>();
            var idx = new List<short>();

            for (int lat = 0; lat <= segments; lat++)
            {
                float theta = lat * MathF.PI / segments;
                for (int lon = 0; lon <= segments; lon++)
                {
                    float phi = lon * 2 * MathF.PI / segments;
                    var n = new Vector3(
                        MathF.Sin(theta) * MathF.Cos(phi),
                        MathF.Cos(theta),
                        MathF.Sin(theta) * MathF.Sin(phi));
                    verts.Add(new(n * radius, color, n));
                }
            }

            for (int lat = 0; lat < segments; lat++)
            {
                for (int lon = 0; lon < segments; lon++)
                {
                    short a = (short)(lat * (segments + 1) + lon);
                    short b = (short)(a + segments + 1);
                    idx.AddRange(new short[] { a, (short)(a+1), b, (short)(a+1), (short)(b+1), b });
                }
            }

            return CreateMesh(gd, verts.ToArray(), idx.ToArray(), new BoundingSphere(Vector3.Zero, radius));
        }

        public static GameMesh CreateCylinder(GraphicsDevice gd, float radius, float height, int segments, Color color)
        {
            var verts = new List<VertexPositionColorNormal>();
            var idx = new List<short>();

            float half = height * 0.5f;
            for (int i = 0; i <= segments; i++)
            {
                float angle = i * 2 * MathF.PI / segments;
                float x = MathF.Cos(angle) * radius;
                float z = MathF.Sin(angle) * radius;
                var n = new Vector3(MathF.Cos(angle), 0, MathF.Sin(angle));
                verts.Add(new(new(x, -half, z), color, n));
                verts.Add(new(new(x,  half, z), color, n));
            }

            for (int i = 0; i < segments; i++)
            {
                short a = (short)(i * 2), b = (short)(a + 1);
                short c = (short)(a + 2), d = (short)(a + 3);
                idx.AddRange(new short[] { a, b, c, b, d, c });
            }

            return CreateMesh(gd, verts.ToArray(), idx.ToArray(),
                new BoundingSphere(Vector3.Zero, MathF.Max(radius, half)));
        }

        public static GameMesh CreateCone(GraphicsDevice gd, float radius, float height, int segments, Color color)
        {
            var verts = new List<VertexPositionColorNormal>();
            var idx = new List<short>();

            verts.Add(new(new(0, height, 0), color, Vector3.Up));
            for (int i = 0; i <= segments; i++)
            {
                float angle = i * 2 * MathF.PI / segments;
                float x = MathF.Cos(angle) * radius;
                float z = MathF.Sin(angle) * radius;
                var n = Vector3.Normalize(new(x, radius, z));
                verts.Add(new(new(x, 0, z), color, n));
            }

            for (int i = 1; i <= segments; i++)
                idx.AddRange(new short[] { 0, (short)(i), (short)(i + 1) });

            return CreateMesh(gd, verts.ToArray(), idx.ToArray(),
                new BoundingSphere(new(0, height * 0.5f, 0), MathF.Max(radius, height)));
        }

        private static GameMesh CreateMesh(GraphicsDevice gd,
            VertexPositionColorNormal[] verts, short[] indices, BoundingSphere bounds)
        {
            var vb = new VertexBuffer(gd, VertexPositionColorNormal.VertexDeclaration,
                verts.Length, BufferUsage.WriteOnly);
            vb.SetData(verts);

            var ib = new IndexBuffer(gd, IndexElementSize.SixteenBits, indices.Length, BufferUsage.WriteOnly);
            ib.SetData(indices);

            return new GameMesh
            {
                VertexBuffer = vb,
                IndexBuffer = ib,
                PrimitiveCount = indices.Length / 3,
                BoundingSphere = bounds
            };
        }

        private static Vector3[] ToV3(VertexPositionColorNormal[] verts)
        {
            var result = new Vector3[verts.Length];
            for (int i = 0; i < verts.Length; i++) result[i] = verts[i].Position;
            return result;
        }
    }
}
