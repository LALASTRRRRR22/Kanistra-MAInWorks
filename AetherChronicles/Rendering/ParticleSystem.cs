using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using System;
using System.Collections.Generic;

namespace AetherChronicles.Rendering
{
    public enum ParticleEffect { Hit, Blood, Magic, Fire, Heal, LevelUp, Death, Explosion }

    public class Particle
    {
        public Vector3 Position;
        public Vector3 Velocity;
        public Color Color;
        public float Life;
        public float MaxLife;
        public float Size;
        public bool Active;

        public float Alpha => Life / MaxLife;
    }

    public class ParticleSystem
    {
        private readonly Particle[] _pool;
        private int _poolIndex = 0;
        private readonly Random _rng = new();

        public ParticleSystem(int maxParticles = 2000)
        {
            _pool = new Particle[maxParticles];
            for (int i = 0; i < maxParticles; i++)
                _pool[i] = new Particle();
        }

        private Particle Spawn(Vector3 position, Vector3 velocity, Color color, float life, float size)
        {
            var p = _pool[_poolIndex % _pool.Length];
            _poolIndex++;
            p.Position = position;
            p.Velocity = velocity;
            p.Color = color;
            p.Life = life;
            p.MaxLife = life;
            p.Size = size;
            p.Active = true;
            return p;
        }

        public void Emit(ParticleEffect effect, Vector3 position)
        {
            switch (effect)
            {
                case ParticleEffect.Hit:
                    for (int i = 0; i < 8; i++)
                        Spawn(position, RandomVelocity(3f), new Color(255, 200, 0), 0.4f, 0.15f);
                    break;
                case ParticleEffect.Blood:
                    for (int i = 0; i < 12; i++)
                        Spawn(position + Vector3.Up, RandomVelocity(4f), new Color(200, 20, 20), 0.6f, 0.1f);
                    break;
                case ParticleEffect.Magic:
                    for (int i = 0; i < 20; i++)
                    {
                        float t = i / 20f * MathF.PI * 2;
                        var vel = new Vector3(MathF.Cos(t), 2f, MathF.Sin(t)) * 2f;
                        Spawn(position, vel, new Color(100, 50, 255), 1.0f, 0.12f);
                    }
                    break;
                case ParticleEffect.Fire:
                    for (int i = 0; i < 15; i++)
                    {
                        var vel = new Vector3(RndRange(-1f, 1f), RndRange(2f, 5f), RndRange(-1f, 1f));
                        var col = new Color(255, (int)RndRange(50, 200), 0);
                        Spawn(position, vel, col, 0.8f, 0.2f);
                    }
                    break;
                case ParticleEffect.Heal:
                    for (int i = 0; i < 15; i++)
                        Spawn(position + Vector3.Up * RndRange(0, 2f),
                            new Vector3(RndRange(-0.5f, 0.5f), 3f, RndRange(-0.5f, 0.5f)),
                            Color.LimeGreen, 1.2f, 0.15f);
                    break;
                case ParticleEffect.LevelUp:
                    for (int i = 0; i < 30; i++)
                    {
                        float a = i / 30f * MathF.PI * 2;
                        var vel = new Vector3(MathF.Cos(a) * 3f, 5f + RndRange(0, 3f), MathF.Sin(a) * 3f);
                        Spawn(position, vel, new Color(255, 215, 0), 2f, 0.2f);
                    }
                    break;
                case ParticleEffect.Death:
                    for (int i = 0; i < 25; i++)
                        Spawn(position + Vector3.Up, RandomVelocity(5f), new Color(80, 0, 100), 1.5f, 0.15f);
                    break;
                case ParticleEffect.Explosion:
                    for (int i = 0; i < 40; i++)
                    {
                        var col = new Color(255, (int)RndRange(100, 255), 0);
                        Spawn(position, RandomVelocity(8f), col, 1.0f, 0.25f);
                    }
                    break;
            }
        }

        public void Update(float dt)
        {
            foreach (var p in _pool)
            {
                if (!p.Active) continue;
                p.Life -= dt;
                if (p.Life <= 0) { p.Active = false; continue; }
                p.Velocity.Y -= 9.8f * dt;
                p.Position += p.Velocity * dt;
            }
        }

        public void Draw(GraphicsDevice gd, BasicEffect effect, Matrix view, Matrix projection)
        {
            effect.View = view;
            effect.Projection = projection;
            effect.VertexColorEnabled = true;
            effect.LightingEnabled = false;

            foreach (var p in _pool)
            {
                if (!p.Active) continue;

                float s = p.Size * p.Alpha;
                var pos = p.Position;

                var verts = new[]
                {
                    new VertexPositionColor(pos + new Vector3(-s, -s, 0), p.Color * p.Alpha),
                    new VertexPositionColor(pos + new Vector3( s, -s, 0), p.Color * p.Alpha),
                    new VertexPositionColor(pos + new Vector3( s,  s, 0), p.Color * p.Alpha),
                    new VertexPositionColor(pos + new Vector3(-s,  s, 0), p.Color * p.Alpha),
                };

                effect.World = Matrix.Identity;
                foreach (var pass in effect.CurrentTechnique.Passes)
                {
                    pass.Apply();
                    gd.DrawUserPrimitives(PrimitiveType.TriangleList, new[]
                    {
                        verts[0], verts[1], verts[2], verts[0], verts[2], verts[3]
                    }, 0, 2);
                }
            }
        }

        private Vector3 RandomVelocity(float speed)
        {
            return new Vector3(RndRange(-1f, 1f), RndRange(0f, 1f), RndRange(-1f, 1f)) * speed;
        }

        private float RndRange(float min, float max) =>
            (float)(_rng.NextDouble() * (max - min) + min);
    }
}
