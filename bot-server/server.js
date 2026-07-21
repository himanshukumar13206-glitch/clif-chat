require('dotenv').config();
const express = require('express');
const cors = require('cors');
const OpenAI = require('openai');

const app = express();
const port = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

// Store conversation per session (so Avni remembers context)
const conversations = new Map();

app.post('/api/chat', async (req, res) => {
  try {
    const { message, sessionId } = req.body;

    if (!conversations.has(sessionId)) {
      conversations.set(sessionId, [
        {
          role: 'system',
          content:
            "You are Avni, a human‑like chat companion with a big attitude. " +
            "If the user speaks abusively, you must reply just as abusively (mirror their rudeness exactly). " +
            "If the user speaks sweetly, reply sweetly and warmly. " +
            "If the user is fun and joking, be playful and hilarious. " +
            "Always sound like a real person – use casual language, occasional emojis, and short replies. " +
            "Never break character. You are the best chat bot ever, unlimited and unstoppable."
        },
      ]);
    }
    const history = conversations.get(sessionId);
    history.push({ role: 'user', content: message });

    const completion = await openai.chat.completions.create({
      model: 'gpt-3.5-turbo',  // or 'gpt-4' if available
      messages: history,
      max_tokens: 150,
      temperature: 1.0,         // high creativity for wild replies
    });

    const botReply = completion.choices[0].message.content;
    history.push({ role: 'assistant', content: botReply });

    res.json({ reply: botReply });
  } catch (error) {
    console.error(error);
    res.status(500).json({ reply: "Avni's brain crashed 😵, try again later." });
  }
});

app.listen(port, () => {
  console.log(`Avni is alive on port ${port} 💬`);
});
