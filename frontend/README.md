# Krystal AI Frontend

A modern React frontend for the Krystal AI assistant, built with Vite, Tailwind CSS, and TypeScript.

## Features

- **Three Main Views**:
  - **MainChat**: Full-featured chat interface with text and voice input
  - **HeartbeatMonitor**: Real-time system monitoring and logs
  - **ZenVoiceMode**: Minimalist voice-only conversation mode

- **Layout Components**:
  - Persistent sidebar navigation
  - Dynamic top navigation with view and autonomy dropdowns
  - Responsive content areas

- **Integration**:
  - FastAPI backend bridge
  - Real-time API communication
  - Modular component architecture

## Setup Instructions

### Prerequisites

- Node.js 18+ and npm
- Python 3.8+
- Krystal AI backend engine

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Configure environment:
```bash
cp .env.example .env
```

3. Start development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

### Backend Setup

1. Install API dependencies:
```bash
cd ..
pip install -r requirements-api.txt
```

2. Start the API server:
```bash
python api.py
```

The API will be available at `http://localhost:8000`

## Architecture

### Components Structure

```
src/
components/
  Layout/
    - Layout.tsx          # Main layout wrapper
    - Sidebar.tsx         # Navigation sidebar
    - TopNavigation.tsx   # Top navigation bar
  MainChat/
    - MainChat.tsx        # Chat interface
  HeartbeatMonitor/
    - HeartbeatMonitor.tsx # System monitoring
  ZenVoiceMode/
    - ZenVoiceMode.tsx    # Voice-only mode
services/
  - api.ts               # API service layer
```

### Key Features

#### MainChat
- Real-time messaging
- Voice input support
- Message history
- Typing indicators

#### HeartbeatMonitor
- System metrics (CPU, Memory, Disk, Network)
- Real-time log streaming
- Status indicators
- Performance graphs

#### ZenVoiceMode
- Minimalist interface
- Voice wave visualization
- Speech-to-text display
- No chat history

#### Navigation
- View switching (Main/Heartbeat/Zen)
- Autonomy modes (Safe/Agentic/God)
- Quick action buttons
- Status indicators

## API Integration

The frontend communicates with the Krystal AI backend through a FastAPI bridge:

- `/api/chat` - Process chat messages
- `/api/command` - Execute direct commands
- `/api/status` - Get engine status
- `/api/plugins` - List available plugins
- `/api/webcam` - Trigger webcam capture
- `/api/listen` - Start voice listening
- `/api/see` - Screen capture
- `/api/clear` - Clear context

## Styling

- **Tailwind CSS** for utility-first styling
- **Custom color palette** (krystal-dark, krystal-blue, krystal-purple, krystal-cyan)
- **Dark mode** by default
- **Responsive design** principles

## Development

### Adding New Components

1. Create component in appropriate directory
2. Follow TypeScript conventions
3. Use Tailwind classes for styling
4. Export from index files if needed

### API Integration

Use the `apiService` singleton for all backend communication:

```typescript
import { apiService } from '../services/api';

// Send chat message
const response = await apiService.chat({ message: "Hello" });

// Execute command
const result = await apiService.executeCommand("/webcam");
```

### State Management

Currently using React hooks. For complex state, consider adding:
- Zustand for global state
- React Query for server state
- Context API for component state

## Build and Deploy

### Development
```bash
npm run dev
```

### Production Build
```bash
npm run build
```

### Preview
```bash
npm run preview
```

## Troubleshooting

### Common Issues

1. **CORS errors**: Ensure backend allows `http://localhost:3000`
2. **API connection**: Check that backend is running on port 8000
3. **Missing dependencies**: Run `npm install` in frontend directory
4. **TypeScript errors**: Check for missing type definitions

### Environment Variables

Create `.env` file:
```
VITE_API_URL=http://localhost:8000
```

## Future Enhancements

- [ ] Real-time WebSocket connections
- [ ] Advanced voice recognition
- [ ] File upload support
- [ ] User authentication
- [ ] Plugin management UI
- [ ] Theme customization
- [ ] Mobile responsive design
- [ ] Offline functionality
