using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Microsoft.Xna.Framework.Input;
using System;

namespace AetherChronicles.Engine
{
    public class Camera3D
    {
        public Matrix View { get; private set; }
        public Matrix Projection { get; private set; }
        public Vector3 Position { get; private set; }
        public Vector3 Target { get; private set; }

        private float _yaw;
        private float _pitch;
        private float _distance = 8f;
        private const float MinDistance = 3f;
        private const float MaxDistance = 20f;
        private const float Sensitivity = 0.003f;

        private MouseState _prevMouse;

        public Camera3D(float aspectRatio)
        {
            Projection = Matrix.CreatePerspectiveFieldOfView(
                MathHelper.ToRadians(60f), aspectRatio, 0.1f, 500f);
            _yaw = 0f;
            _pitch = MathHelper.ToRadians(25f);
        }

        public void Update(Vector3 targetPosition, GameTime gameTime)
        {
            var mouse = Mouse.GetState();

            if (mouse.RightButton == ButtonState.Pressed)
            {
                float dx = mouse.X - _prevMouse.X;
                float dy = mouse.Y - _prevMouse.Y;
                _yaw -= dx * Sensitivity;
                _pitch = MathHelper.Clamp(_pitch + dy * Sensitivity,
                    MathHelper.ToRadians(5f), MathHelper.ToRadians(70f));
            }

            int scrollDelta = mouse.ScrollWheelValue - _prevMouse.ScrollWheelValue;
            _distance = MathHelper.Clamp(_distance - scrollDelta * 0.01f, MinDistance, MaxDistance);

            _prevMouse = mouse;

            float camX = (float)(targetPosition.X + _distance * Math.Cos(_pitch) * Math.Sin(_yaw));
            float camY = (float)(targetPosition.Y + _distance * Math.Sin(_pitch));
            float camZ = (float)(targetPosition.Z + _distance * Math.Cos(_pitch) * Math.Cos(_yaw));

            Position = new Vector3(camX, camY, camZ);
            Target = targetPosition + Vector3.Up * 1.5f;
            View = Matrix.CreateLookAt(Position, Target, Vector3.Up);
        }

        public void SetAspectRatio(float aspectRatio)
        {
            Projection = Matrix.CreatePerspectiveFieldOfView(
                MathHelper.ToRadians(60f), aspectRatio, 0.1f, 500f);
        }

        public Ray GetPickingRay(Vector2 screenPos, Viewport viewport)
        {
            Vector3 nearPoint = viewport.Unproject(new Vector3(screenPos, 0), Projection, View, Matrix.Identity);
            Vector3 farPoint = viewport.Unproject(new Vector3(screenPos, 1), Projection, View, Matrix.Identity);
            Vector3 dir = Vector3.Normalize(farPoint - nearPoint);
            return new Ray(nearPoint, dir);
        }

        public float Yaw => _yaw;
    }
}
