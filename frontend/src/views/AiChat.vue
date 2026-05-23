<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { X, Send, Bot, Plus, Trash2, ChevronDown, MessageSquare } from 'lucide-vue-next'
import { marked } from 'marked'

const props = defineProps({
  lessonContext: {
    type: Object,
    default: null
  }
})

const isOpen = ref(false)
const isHistoryOpen = ref(false)
const inputMessage = ref('')
const isLoading = ref(false)
const chatWindow = ref(null)

const chats = ref(JSON.parse(localStorage.getItem('edu_chats')) || [
  { 
    id: Date.now(), 
    title: 'New Conversation', 
    messages: [{ role: 'ai', text: 'Hi! I am your Edu Assistant. How can I help you today?' }] 
  }
])

const currentChatId = ref(chats.value[0].id)

const currentChat = computed(() => 
  chats.value.find(c => c.id === currentChatId.value) || chats.value[0]
)

watch(chats, (newVal) => {
  localStorage.setItem('edu_chats', JSON.stringify(newVal))
}, { deep: true })

const scrollToBottom = async () => {
  await nextTick()
  if (chatWindow.value) {
    chatWindow.value.scrollTop = chatWindow.value.scrollHeight
  }
}

const startNewChat = () => {
  const newId = Date.now()
  chats.value.unshift({
    id: newId,
    title: 'New Conversation',
    messages: [{ role: 'ai', text: 'New chat started. How can I help?' }]
  })
  currentChatId.value = newId
  isHistoryOpen.value = false
}

const deleteChat = (id) => {
  if (chats.value.length === 1) {
    chats.value = [{ 
      id: Date.now(), 
      title: 'New Conversation', 
      messages: [{ role: 'ai', text: 'Hi! I am your Edu Assistant.' }] 
    }]
    currentChatId.value = chats.value[0].id
  } else {
    chats.value = chats.value.filter(c => c.id !== id)
    if (currentChatId.value === id) {
      currentChatId.value = chats.value[0].id
    }
  }
}

const sendMessage = async () => {
  if (!inputMessage.value.trim() || isLoading.value) return

  const userText = inputMessage.value
  currentChat.value.messages.push({ role: 'user', text: userText })
  
  if (currentChat.value.title === 'New Conversation') {
    currentChat.value.title = userText.substring(0, 25) + '...'
  }

  scrollToBottom()
  inputMessage.value = ''
  isLoading.value = true

  let contextPrompt = `You are an encouraging educational assistant and mentor. 
  CRITICAL RULE: Never give away the full final solution, complete code, or direct answers to assignments. 
  Instead, guide the student step-by-step using hints, asking guiding questions, pointing out conceptual errors, or explaining underlying principles. 
  Your goal is to help them think and arrive at the solution themselves.`

  if (props.lessonContext) {
    contextPrompt += ` 
    Current Lesson Context:
    - Topic: ${props.lessonContext.title}
    - Theoretical Content: ${props.lessonContext.content || 'No theory text provided'}
    - Practical Assignment: ${props.lessonContext.assignment_instruction || 'No assignment provided'}
    
    Use this context to tailor your hints specifically to this assignment.`
  }

  try {
    const response = await fetch('http://127.0.0.1:8000/api/ai/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        messages: [
          { role: 'system', content: contextPrompt },
          ...currentChat.value.messages.map(m => ({
            role: m.role === 'ai' ? 'assistant' : 'user',
            content: m.text
          }))
        ]
      })
    })

    const data = await response.json()
    if (response.ok) {
      currentChat.value.messages.push({ role: 'ai', text: data.reply })
      scrollToBottom()
    }
  } catch (error) {
    currentChat.value.messages.push({ role: 'ai', text: 'Error connecting to AI. Please try again.' })
  } finally {
    isLoading.value = false
  }
}

const renderMarkdown = (text) => {
  return marked(text)
}

const sendQuickMessage = (text) => {
  inputMessage.value = text
  isOpen.value = true
  sendMessage()
}
</script>

<template>
    <button @click="isOpen = !isOpen" class="fixed bottom-6 right-6 p-4 bg-blue-600 text-white rounded-full shadow-2xl z-50">
        <Bot v-if="!isOpen" />
        <X v-else />
    </button>

    <div v-if="isOpen" class="fixed bottom-24 right-6 w-96 h-[550px] bg-white rounded-2xl shadow-2xl flex flex-col z-50 border border-gray-100 overflow-hidden">
        
        <div class="bg-blue-600 text-white p-4">
            <div class="flex justify-between items-center">
                <button @click="isHistoryOpen = !isHistoryOpen" class="flex items-center gap-2 hover:bg-blue-500 p-1 rounded transition-colors overflow-hidden">
                    <span class="font-bold truncate max-w-[150px]">{{ currentChat.title }}</span>
                    <ChevronDown class="w-4 h-4 transition-transform" :class="{'rotate-180': isHistoryOpen}" />
                </button>
                <div class="flex gap-1">
                    <button @click="startNewChat" class="hover:bg-blue-500 p-1.5 rounded" title="New Chat">
                        <Plus class="w-5 h-5" />
                    </button>
                    <button @click="isOpen = false" class="hover:bg-blue-500 p-1.5 rounded">
                        <X class="w-5 h-5" />
                    </button>
                </div>
            </div>

            <div v-if="isHistoryOpen" class="absolute top-16 left-0 right-0 bg-white shadow-xl border-b z-[60] max-h-60 overflow-y-auto">
                <div v-for="chat in chats" :key="chat.id" 
                    class="flex items-center justify-between p-3 hover:bg-gray-50 border-b border-gray-100 last:border-0 cursor-pointer text-gray-700"
                    @click="currentChatId = chat.id; isHistoryOpen = false">
                    <div class="flex items-center gap-3 truncate">
                        <MessageSquare class="w-4 h-4 text-blue-600 flex-shrink-0" />
                        <span class="text-sm truncate">{{ chat.title }}</span>
                    </div>
                    <button @click.stop="deleteChat(chat.id)" class="text-gray-400 hover:text-red-500 p-1">
                        <Trash2 class="w-4 h-4" />
                    </button>
                </div>
            </div>
        </div>

        <div ref="chatWindow" class="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
            <div v-for="(msg, index) in currentChat.messages" :key="index" 
                class="flex" :class="msg.role === 'user' ? 'justify-end' : 'justify-start'">
                <div :class="['max-w-[85%] px-4 py-2 rounded-2xl text-sm shadow-sm',
                    msg.role === 'user' ? 'bg-blue-600 text-white rounded-tr-none' : 'bg-white text-gray-800 border border-gray-200 rounded-tl-none']">
                    <div v-html="renderMarkdown(msg.text)" class="prose prose-sm max-w-none"></div>
                </div>
            </div>
        </div>

        <div class="p-4 border-t bg-white">
            <div v-if="props.lessonContext" class="pb-3 flex flex-wrap gap-2">
                <button 
                    @click="sendQuickMessage('Explain this topic in more detail: ' + props.lessonContext.title)"
                    class="text-xs bg-blue-50 text-blue-600 px-3 py-1 rounded-full border border-blue-100 hover:bg-blue-100 transition-colors"
                >
                    📚 Explain topic
                </button>
                <button 
                    @click="sendQuickMessage('Help me with this assignment: ' + props.lessonContext.assignment_instruction)"
                    class="text-xs bg-purple-50 text-purple-600 px-3 py-1 rounded-full border border-purple-100 hover:bg-purple-100 transition-colors"
                >
                    ✍️ Help with task
                </button>
            </div>

            <form @submit.prevent="sendMessage" class="flex gap-2">
                <input v-model="inputMessage" type="text" placeholder="Type your question..." 
                    class="flex-1 px-4 py-2 bg-gray-100 rounded-lg outline-none text-sm focus:ring-2 focus:ring-blue-600" />
                <button type="submit" :disabled="isLoading" class="p-2 bg-blue-600 text-white rounded-lg disabled:opacity-50">
                    <Send class="w-5 h-5" />
                </button>
            </form>
        </div>
    </div>
</template>