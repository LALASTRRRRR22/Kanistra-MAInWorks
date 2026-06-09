using Microsoft.Xna.Framework.Input;

namespace AetherChronicles.Engine
{
    public class InputManager
    {
        private KeyboardState _current;
        private KeyboardState _previous;
        private MouseState _currentMouse;
        private MouseState _previousMouse;

        public void Update()
        {
            _previous = _current;
            _current = Keyboard.GetState();
            _previousMouse = _currentMouse;
            _currentMouse = Mouse.GetState();
        }

        public bool IsDown(Keys key) => _current.IsKeyDown(key);
        public bool IsUp(Keys key) => _current.IsKeyUp(key);
        public bool JustPressed(Keys key) => _current.IsKeyDown(key) && _previous.IsKeyUp(key);
        public bool JustReleased(Keys key) => _current.IsKeyUp(key) && _previous.IsKeyDown(key);

        public bool MouseLeftJustPressed =>
            _currentMouse.LeftButton == ButtonState.Pressed &&
            _previousMouse.LeftButton == ButtonState.Released;

        public bool MouseLeftDown => _currentMouse.LeftButton == ButtonState.Pressed;
        public bool MouseRightDown => _currentMouse.RightButton == ButtonState.Pressed;

        public int MouseX => _currentMouse.X;
        public int MouseY => _currentMouse.Y;
        public int ScrollDelta => _currentMouse.ScrollWheelValue - _previousMouse.ScrollWheelValue;
    }
}
