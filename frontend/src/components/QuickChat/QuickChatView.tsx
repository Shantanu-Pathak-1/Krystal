import React, { useState, useEffect, useRef } from 'react';
import { Globe, Eye, Paperclip, Send, Minus, X } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

const QuickChatView: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isWebEnabled, setIsWebEnabled] = useState(false);
  const [isVisionEnabled, setIsVisionEnabled] = useState(false);
  const [attachedFile, setAttachedFile] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Cleanup function: Clear messages when window is hidden/unmounted
    return () => {
      setMessages([]);
      setIsWebEnabled(false);
      setIsVisionEnabled(false);
      setAttachedFile(null);
    };
  }, []);

  const handleSendMessage = async () => {
    if (!inputValue.trim() && !attachedFile) return;

    const userMessage = inputValue.trim();
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          use_web: isWebEnabled,
          use_vision: isVisionEnabled,
          file: attachedFile,
          mode: 'Agentic'
        }),
      });

      const data = await response.json();
      if (data.response) {
        setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      setMessages(prev => [...prev, { role: 'assistant', content: 'Error: Could not connect to the neural core.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleClose = () => {
    try {
      const { ipcRenderer } = require('electron');
      ipcRenderer.send('quick-chat-hide');
    } catch (e) {
      window.close();
    }
  };

  const handleMinimize = () => {
    try {
      const { ipcRenderer } = require('electron');
      ipcRenderer.send('quick-chat-minimize');
    } catch (e) {
      console.error('Failed to minimize:', e);
    }
  };

  return (
    <div className="h-screen w-screen bg-[#030712]/90 backdrop-blur-lg flex flex-col text-emerald-400 p-4 border border-emerald-900/50 overflow-hidden" style={{ borderRadius: '12px' }}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4 flex-shrink-0" style={{ WebkitAppRegion: 'drag' as any }}>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_#10b981]"></div>
          <h1 className="text-sm font-bold tracking-widest uppercase italic opacity-80">Krystal Quick Chat</h1>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleMinimize}
            className="p-1.5 rounded-lg transition-all duration-200 hover:bg-emerald-900/30"
            style={{ WebkitAppRegion: 'no-drag' as any }}
            title="Minimize"
          >
            <Minus size={14} className="text-emerald-400" />
          </button>
          <button
            onClick={handleClose}
            className="p-1.5 rounded-lg transition-all duration-200 hover:bg-red-900/30"
            style={{ WebkitAppRegion: 'no-drag' as any }}
            title="Close"
          >
            <X size={14} className="text-emerald-400" />
          </button>
        </div>
      </div>
      
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-2 custom-scrollbar mb-4">
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center opacity-30 text-center px-8">
            <div className="w-12 h-12 border border-emerald-500/20 rounded-full flex items-center justify-center mb-4">
              <Globe size={20} className="animate-pulse" />
            </div>
            <p className="text-xs uppercase tracking-[0.2em]">Neural Link Standby</p>
            <p className="text-[10px] mt-2 leading-relaxed">System ready for localized query execution.</p>
          </div>
        )}
        
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] p-3 rounded-lg text-xs leading-relaxed ${
              msg.role === 'user' 
                ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-200' 
                : 'bg-black/40 border border-emerald-900/30 text-emerald-400'
            }`}>
              {msg.content}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-black/40 border border-emerald-900/30 p-3 rounded-lg flex gap-1">
              <span className="w-1 h-1 bg-emerald-500 rounded-full animate-bounce"></span>
              <span className="w-1 h-1 bg-emerald-500 rounded-full animate-bounce [animation-delay:0.2s]"></span>
              <span className="w-1 h-1 bg-emerald-500 rounded-full animate-bounce [animation-delay:0.4s]"></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="mt-auto pt-4 border-t border-emerald-900/30 flex-shrink-0">
        <div className="relative group">
          <textarea 
            rows={1}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Type a command..." 
            className="w-full bg-black/60 border border-emerald-900/50 rounded-lg py-3 pl-4 pr-12 text-sm text-emerald-400 placeholder-emerald-900/50 focus:outline-none focus:border-emerald-500/50 transition-all resize-none min-h-[44px] max-h-32"
          />
          <button 
            onClick={handleSendMessage}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-emerald-600 hover:text-emerald-400 transition-colors"
          >
            <Send size={18} />
          </button>
        </div>

        {/* Superpower Buttons */}
        <div className="flex items-center gap-3 mt-3 px-1">
          <button 
            onClick={() => setIsWebEnabled(!isWebEnabled)}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-md border transition-all ${
              isWebEnabled 
                ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300' 
                : 'bg-transparent border-emerald-900/30 text-emerald-900 hover:border-emerald-700/50 hover:text-emerald-700'
            }`}
          >
            <Globe size={14} />
            <span className="text-[10px] font-bold uppercase tracking-wider">Web</span>
          </button>

          <button 
            onClick={() => setIsVisionEnabled(!isVisionEnabled)}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-md border transition-all ${
              isVisionEnabled 
                ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300' 
                : 'bg-transparent border-emerald-900/30 text-emerald-900 hover:border-emerald-700/50 hover:text-emerald-700'
            }`}
          >
            <Eye size={14} />
            <span className="text-[10px] font-bold uppercase tracking-wider">Vision</span>
          </button>

          <button 
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md border border-emerald-900/30 text-emerald-900 hover:border-emerald-700/50 hover:text-emerald-700 transition-all ml-auto"
          >
            <Paperclip size={14} />
            <span className="text-[10px] font-bold uppercase tracking-wider">Attach</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default QuickChatView;
