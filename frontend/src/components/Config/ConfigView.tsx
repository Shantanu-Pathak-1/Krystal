import { useState, useEffect } from 'react'
import { Settings, Save, RotateCcw, Shield, Database, Key, Eye, EyeOff } from 'lucide-react'

interface ConfigSection {
  id: string
  title: string
  icon: any
  fields: ConfigField[]
}

interface ConfigField {
  id: string
  label: string
  type: 'text' | 'password' | 'number' | 'select' | 'toggle' | 'textarea'
  value: any
  placeholder?: string
  description?: string
  options?: { value: string; label: string }[]
  required?: boolean
}

export default function ConfigView() {
  const [config, setConfig] = useState<Record<string, any>>({})
  const [isLoading, setIsLoading] = useState(false)
  const [hasChanges, setHasChanges] = useState(false)
  const [showPasswords, setShowPasswords] = useState<Record<string, boolean>>({})

  const configSections: ConfigSection[] = [
    {
      id: 'api',
      title: 'API Configuration',
      icon: Key,
      fields: [
        {
          id: 'openai_api_key',
          label: 'OpenAI API Key',
          type: 'password',
          value: config.openai_api_key || '',
          placeholder: 'sk-...',
          description: 'Your OpenAI API key for LLM processing',
          required: true,
        },
        {
          id: 'groq_api_key',
          label: 'Groq API Key',
          type: 'password',
          value: config.groq_api_key || '',
          placeholder: 'gsk_...',
          description: 'Groq API key for fast inference',
        },
        {
          id: 'anthropic_api_key',
          label: 'Anthropic API Key',
          type: 'password',
          value: config.anthropic_api_key || '',
          placeholder: 'sk-ant-...',
          description: 'Anthropic API key for Claude models',
        },
        {
          id: 'api_timeout',
          label: 'API Timeout (seconds)',
          type: 'number',
          value: config.api_timeout || 30,
          description: 'Request timeout for API calls',
        },
      ],
    },
    {
      id: 'database',
      title: 'Database Configuration',
      icon: Database,
      fields: [
        {
          id: 'mongodb_uri',
          label: 'MongoDB URI',
          type: 'text',
          value: config.mongodb_uri || 'mongodb://localhost:27017',
          description: 'MongoDB connection string for chat history',
        },
        {
          id: 'pinecone_api_key',
          label: 'Pinecone API Key',
          type: 'password',
          value: config.pinecone_api_key || '',
          placeholder: '...',
          description: 'Pinecone API key for vector storage',
        },
        {
          id: 'pinecone_environment',
          label: 'Pinecone Environment',
          type: 'select',
          value: config.pinecone_environment || 'us-west1-gcp',
          options: [
            { value: 'us-west1-gcp', label: 'US West 1 (GCP)' },
            { value: 'us-east1-gcp', label: 'US East 1 (GCP)' },
            { value: 'eu-west1-gcp', label: 'Europe West 1 (GCP)' },
          ],
          description: 'Pinecone environment region',
        },
      ],
    },
    {
      id: 'system',
      title: 'System Settings',
      icon: Settings,
      fields: [
        {
          id: 'system_prompt',
          label: 'System Prompt',
          type: 'textarea',
          value: config.system_prompt || 'You are Krystal, an AI assistant...',
          description: 'Default system prompt for the AI',
        },
        {
          id: 'max_tokens',
          label: 'Max Tokens',
          type: 'number',
          value: config.max_tokens || 2048,
          description: 'Maximum tokens for AI responses',
        },
        {
          id: 'temperature',
          label: 'Temperature',
          type: 'number',
          value: config.temperature || 0.7,
          description: 'AI response creativity (0.0-1.0)',
        },
        {
          id: 'enable_voice',
          label: 'Enable Voice Input',
          type: 'toggle',
          value: config.enable_voice !== false,
          description: 'Allow voice input for commands',
        },
        {
          id: 'enable_webcam',
          label: 'Enable Webcam',
          type: 'toggle',
          value: config.enable_webcam !== false,
          description: 'Allow webcam access for visual input',
        },
      ],
    },
    {
      id: 'security',
      title: 'Security Settings',
      icon: Shield,
      fields: [
        {
          id: 'require_auth',
          label: 'Require Authentication',
          type: 'toggle',
          value: config.require_auth || false,
          description: 'Require user authentication for access',
        },
        {
          id: 'allowed_origins',
          label: 'Allowed Origins',
          type: 'text',
          value: config.allowed_origins || 'http://localhost:3000',
          description: 'CORS allowed origins (comma-separated)',
        },
        {
          id: 'log_level',
          label: 'Log Level',
          type: 'select',
          value: config.log_level || 'INFO',
          options: [
            { value: 'DEBUG', label: 'Debug' },
            { value: 'INFO', label: 'Info' },
            { value: 'WARNING', label: 'Warning' },
            { value: 'ERROR', label: 'Error' },
          ],
          description: 'System logging level',
        },
      ],
    },
  ]

  useEffect(() => {
    loadConfig()
  }, [])

  const loadConfig = async () => {
    setIsLoading(true)
    try {
      // TODO: Replace with actual API call
      // const response = await apiService.getConfig()
      // setConfig(response.config)
      
      // Mock config for now
      const mockConfig = {
        openai_api_key: '',
        groq_api_key: '',
        anthropic_api_key: '',
        api_timeout: 30,
        mongodb_uri: 'mongodb://localhost:27017',
        pinecone_api_key: '',
        pinecone_environment: 'us-west1-gcp',
        system_prompt: 'You are Krystal, an AI assistant designed to help users with various tasks through natural language conversation and system integration.',
        max_tokens: 2048,
        temperature: 0.7,
        enable_voice: true,
        enable_webcam: true,
        require_auth: false,
        allowed_origins: 'http://localhost:3000',
        log_level: 'INFO',
      }
      setConfig(mockConfig)
    } catch (error) {
      console.error('Failed to load config:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const updateConfig = (fieldId: string, value: any) => {
    setConfig(prev => ({
      ...prev,
      [fieldId]: value,
    }))
    setHasChanges(true)
  }

  const saveConfig = async () => {
    setIsLoading(true)
    try {
      // TODO: Replace with actual API call
      // await apiService.updateConfig(config)
      
      console.log('Config saved:', config)
      setHasChanges(false)
    } catch (error) {
      console.error('Failed to save config:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const resetConfig = async () => {
    if (confirm('Are you sure you want to reset all configuration to defaults?')) {
      await loadConfig()
      setHasChanges(false)
    }
  }

  const togglePasswordVisibility = (fieldId: string) => {
    setShowPasswords(prev => ({
      ...prev,
      [fieldId]: !prev[fieldId],
    }))
  }

  const renderField = (field: ConfigField) => {
    const commonClasses = "w-full px-3 py-2 bg-gray-800 text-white rounded border border-gray-700 focus:border-krystal-purple focus:outline-none"

    switch (field.type) {
      case 'text':
      case 'number':
        return (
          <input
            type={field.type}
            value={field.value}
            onChange={(e) => updateConfig(field.id, field.type === 'number' ? Number(e.target.value) : e.target.value)}
            placeholder={field.placeholder}
            className={commonClasses}
          />
        )

      case 'password':
        return (
          <div className="relative">
            <input
              type={showPasswords[field.id] ? 'text' : 'password'}
              value={field.value}
              onChange={(e) => updateConfig(field.id, e.target.value)}
              placeholder={field.placeholder}
              className={`${commonClasses} pr-10`}
            />
            <button
              type="button"
              onClick={() => togglePasswordVisibility(field.id)}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white"
            >
              {showPasswords[field.id] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
        )

      case 'select':
        return (
          <select
            value={field.value}
            onChange={(e) => updateConfig(field.id, e.target.value)}
            className={commonClasses}
          >
            {field.options?.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        )

      case 'toggle':
        return (
          <button
            type="button"
            onClick={() => updateConfig(field.id, !field.value)}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              field.value ? 'bg-krystal-purple' : 'bg-gray-600'
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                field.value ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        )

      case 'textarea':
        return (
          <textarea
            value={field.value}
            onChange={(e) => updateConfig(field.id, e.target.value)}
            placeholder={field.placeholder}
            rows={4}
            className={`${commonClasses} resize-none`}
          />
        )

      default:
        return null
    }
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Configuration</h1>
          <p className="text-gray-400">Manage Krystal AI system settings and API keys</p>
        </div>
        
        <div className="flex items-center space-x-3">
          <button
            onClick={resetConfig}
            className="flex items-center space-x-2 px-4 py-2 bg-gray-800 text-gray-300 rounded-lg hover:bg-gray-700 transition-colors"
          >
            <RotateCcw className="w-4 h-4" />
            <span>Reset</span>
          </button>
          <button
            onClick={saveConfig}
            disabled={!hasChanges || isLoading}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
              hasChanges && !isLoading
                ? 'bg-krystal-purple text-white hover:bg-krystal-purple/90'
                : 'bg-gray-700 text-gray-500 cursor-not-allowed'
            }`}
          >
            <Save className="w-4 h-4" />
            <span>{isLoading ? 'Saving...' : 'Save Changes'}</span>
          </button>
        </div>
      </div>

      {/* Configuration Sections */}
      <div className="space-y-6">
        {configSections.map((section) => {
          const Icon = section.icon
          return (
            <div key={section.id} className="bg-gray-800 rounded-lg border border-gray-700">
              <div className="p-6 border-b border-gray-700">
                <div className="flex items-center space-x-3">
                  <Icon className="w-6 h-6 text-krystal-purple" />
                  <h2 className="text-xl font-semibold text-white">{section.title}</h2>
                </div>
              </div>
              
              <div className="p-6 space-y-6">
                {section.fields.map((field) => (
                  <div key={field.id}>
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-white font-medium">
                        {field.label}
                        {field.required && <span className="text-red-400 ml-1">*</span>}
                      </label>
                      {field.type === 'toggle' && (
                        <span className={`text-sm ${
                          field.value ? 'text-green-400' : 'text-gray-400'
                        }`}>
                          {field.value ? 'Enabled' : 'Disabled'}
                        </span>
                      )}
                    </div>
                    
                    {renderField(field)}
                    
                    {field.description && (
                      <p className="text-sm text-gray-400 mt-2">{field.description}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )
        })}
      </div>

      {/* Status Bar */}
      <div className="mt-6 p-4 bg-gray-800 rounded-lg border border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${hasChanges ? 'bg-yellow-400' : 'bg-green-400'}`}></div>
            <span className="text-sm text-gray-300">
              {hasChanges ? 'Unsaved changes' : 'All changes saved'}
            </span>
          </div>
          
          <div className="text-sm text-gray-400">
            Last saved: {new Date().toLocaleString()}
          </div>
        </div>
      </div>
    </div>
  )
}
