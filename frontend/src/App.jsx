import { useState } from 'react'

function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  const sendMessage = async () => {
    if (!input.trim()) return

    const userMessage = { role: 'user', content: input }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input })
      })

      const data = await response.json()
      const agentMessage = { role: 'agent', content: data.message }
      setMessages(prev => [...prev, agentMessage])
    } catch (error) {
      console.error('Error:', error)
      setMessages(prev => [...prev, {
        role: 'agent',
        content: '❌ Backend not running'
      }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      height: '100vh',
      backgroundColor: '#111827',
      color: 'white',
      display: 'flex',
      flexDirection: 'column'
    }}>
      
      {/* Messages */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '2rem',
        maxWidth: '800px',
        width: '100%',
        margin: '0 auto'
      }}>
        {messages.length === 0 && (
          <div style={{ 
            color: '#6B7280', 
            textAlign: 'center', 
            marginTop: '8rem',
            fontSize: '0.875rem'
          }}>
            Type a message to start
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} style={{ marginBottom: '1.5rem' }}>
            <div style={{
              color: '#9CA3AF',
              fontSize: '0.75rem',
              marginBottom: '0.25rem',
              textTransform: 'uppercase',
              letterSpacing: '0.05em'
            }}>
              {msg.role === 'user' ? 'You' : 'Agent'}
            </div>
            <div style={{
              color: 'white',
              fontSize: '1rem',
              lineHeight: '1.625'
            }}>
              {msg.content}
            </div>
          </div>
        ))}

        {loading && (
          <div style={{ marginBottom: '1.5rem' }}>
            <div style={{
              color: '#9CA3AF',
              fontSize: '0.75rem',
              marginBottom: '0.25rem',
              textTransform: 'uppercase'
            }}>
              Agent
            </div>
            <div style={{ color: '#6B7280' }}>Thinking...</div>
          </div>
        )}
      </div>

      {/* Input */}
      <div style={{
        borderTop: '1px solid #1F2937',
        padding: '1.5rem'
      }}>
        <div style={{
          maxWidth: '800px',
          width: '100%',
          margin: '0 auto',
          display: 'flex',
          gap: '0.75rem'
        }}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && !loading && sendMessage()}
            placeholder="Type your message..."
            disabled={loading}
            style={{
              flex: 1,
              backgroundColor: '#1F2937',
              color: 'white',
              padding: '0.75rem 1rem',
              borderRadius: '0.375rem',
              border: '1px solid #374151',
              outline: 'none',
              fontSize: '1rem'
            }}
          />
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            style={{
              backgroundColor: '#000000',
              color: 'white',
              padding: '0.75rem 2rem',
              borderRadius: '0.375rem',
              fontWeight: '500',
              border: 'none',
              cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
              opacity: loading || !input.trim() ? 0.5 : 1,
              transition: 'all 0.2s'
            }}
          >
            Submit
          </button>
        </div>
      </div>
    </div>
  )
}

export default App
