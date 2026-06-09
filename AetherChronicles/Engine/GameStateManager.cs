using System.Collections.Generic;

namespace AetherChronicles.Engine
{
    public enum GameState
    {
        MainMenu,
        Playing,
        Paused,
        Inventory,
        GameOver,
        Victory,
        Cutscene,
        Loading
    }

    public class GameStateManager
    {
        private readonly Stack<GameState> _stateStack = new();

        public GameState Current => _stateStack.Count > 0 ? _stateStack.Peek() : GameState.MainMenu;
        public bool IsPlaying => Current == GameState.Playing;

        public GameStateManager()
        {
            _stateStack.Push(GameState.MainMenu);
        }

        public void Push(GameState state) => _stateStack.Push(state);

        public void Pop()
        {
            if (_stateStack.Count > 1)
                _stateStack.Pop();
        }

        public void Change(GameState state)
        {
            _stateStack.Clear();
            _stateStack.Push(state);
        }
    }
}
