<script setup>
import { ref, onMounted, watch } from 'vue'
import { BookOpen, Mail, Lock, User } from 'lucide-vue-next'
import { useRouter } from 'vue-router'

const router = useRouter()

const email = ref('')
const password = ref('')

const emailError = ref('')
const passwordError = ref('')

const isLoginMode = ref(true)
const generalError = ref('')

const name = ref('')
const nameError = ref('')
const selectedRole = ref('') 

const showSuccess = ref(false)

const isValidEmail = (email) => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

watch(selectedRole, (newRole) => {
    if (newRole) {
        localStorage.setItem('userRole', newRole)
    } else {
        localStorage.removeItem('userRole')
    }
})

const handleLogin = async () => {
    emailError.value = ''
    passwordError.value = ''

    let isValid = true
    if (!email.value) {
        emailError.value = 'Email is required.'
        isValid = false
    }
    if (!password.value) {
        passwordError.value = 'Password is required.'
        isValid = false
    }

    if (!isValid) return

    try {
        const response = await fetch('http://127.0.0.1:8000/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                email: email.value,
                password: password.value
            })
        })

        const data = await response.json()

        if (response.ok) {
            localStorage.setItem('isLoggedIn', 'true')
            localStorage.setItem('userId', data.id)
            localStorage.setItem('userName', data.name)
            localStorage.setItem('userRole', data.role)

            await router.push({ 
                path: '/dashboard', 
                query: { role: data.role }
            })
        } else {
            passwordError.value = data.detail || 'Invalid email or password'
        }
    } catch (err) {
        console.error("Login error:", err)
        passwordError.value = "Server connection failed. Try again later."
    }
}

const handleRegister = async () => {
    nameError.value = ''
    emailError.value = ''
    passwordError.value = ''

    let isValid = true

    if (!name.value) {
        nameError.value = 'Name is required.'
        isValid = false
    }
    if (!email.value) {
    emailError.value = 'Email is required.'
    isValid = false
    } else if (!isValidEmail(email.value)) {
        emailError.value = 'Please enter a valid email (example@gmail.com)'
        isValid = false
    }
    if (!password.value) {
        passwordError.value = 'Password is required.'
        isValid = false
    }
    if (!selectedRole.value) {
        generalError.value = 'Please select your role.'
        isValid = false
    }

    if (!isValid) return

    try {
        const response = await fetch('http://127.0.0.1:8000/api/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                name: name.value,
                email: email.value,
                password: password.value,
                role: selectedRole.value
            })
        })

        const data = await response.json()

        if (response.ok) {

            showSuccess.value = true

            localStorage.setItem('isLoggedIn', 'true')
            localStorage.setItem('userId', data.id)
            localStorage.setItem('userName', data.name)
            localStorage.setItem('userRole', data.role)

            setTimeout(() => {
                showSuccess.value = false
                router.push({ 
                    path: '/dashboard', 
                    query: { role: data.role }
                })
            }, 1000)
        } else {
            if (data.errors) {
                if (data.errors.email) emailError.value = data.errors.email[0]
                if (data.errors.password) passwordError.value = data.errors.password[0]
                if (data.errors.name) nameError.value = data.errors.name[0]
            } else if (data.message) {
                passwordError.value = data.message
            }
        }
    } catch (err) {
        console.error("Registration error:", err)
        passwordError.value = "Connection failed. Please check your server."
    }
}

const toggleMode = () => {
    isLoginMode.value = !isLoginMode.value
    emailError.value = ''
    passwordError.value = ''
}
</script>

<template>
    <div class="flex flex-col min-h-screen bg-blue-50 items-center justify-center">
        <div class="flex flex-col items-center mb-10">
            <div class="bg-blue-600 p-3 rounded-full">
              <BookOpen class="w-12 h-12 text-white" />
            </div>
            <h1 class="text-3xl font-bold p-5">EduPlatform</h1>
        </div>
        <div class="bg-white rounded-3xl shadow-xl shadow-blue-100 p-10 w-full max-w-md border border-blue-50/50">
            <div class="flex flex-col gap-4 w-full">
                <div class="mb-2">
                    <h2 class="text-2xl font-bold text-gray-800 text-center">
                        {{ isLoginMode ? 'Login' : 'Create Account' }}
                    </h2>
                </div>
                <div v-if="!isLoginMode" class="flex flex-col gap-1">
                    <label class="block text-sm font-medium text-gray-700">Full Name</label>
                    <div class="relative">
                        <User class="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                        <input 
                        v-model="name" 
                        type="text" 
                        placeholder="John Doe"
                        class="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-transparent outline-none transition-all"
                        :class="nameError ? 'border-red-500 ring-1 ring-red-500' : 'border-gray-300'"
                        >
                    </div>
                    <p v-if="nameError" class="text-red-500 text-xs font-medium">{{ nameError }}</p>
                </div>
                <div class="flex flex-col gap-1">
                    <label class="block text-sm font-medium text-gray-700">
                        Email
                    </label>
                    <div class="relative">
                        <Mail class="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                        <input v-model="email" 
                        :class="emailError ? 'border-red-500 ring-1 ring-red-500' : 'border-gray-300'" 
                        type="email" 
                        required placeholder="you@email.com" 
                        class="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-transparent">
                    </div>
                </div>
                <p v-if="emailError" class="text-red-500 text-sm font-medium animate-pulse">
                    {{ emailError }}
                </p>
                <div class="flex flex-col gap-1">
                    <label class="block text-sm font-medium text-gray-700">
                        Password
                    </label>
                    <div class="relative">
                        <Lock class="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                        <input v-model="password" 
                        :class="passwordError ? 'border-red-500 ring-1 ring-red-500' : 'border-gray-300'" 
                        type="password" 
                        required placeholder="*******" 
                        class="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-transparent">
                    </div>
                </div>
                <p v-if="passwordError" class="text-red-500 text-sm font-medium animate-pulse">
                    {{ passwordError }}
                </p>
                <div v-if="!isLoginMode" class="flex flex-col gap-2">
                    <label class="block text-sm font-medium text-gray-700">I am a:</label>
                    <div class="grid grid-cols-2 gap-3">
                        <button 
                        @click="selectedRole = 'student'"
                        type="button"
                        class="py-2 px-4 rounded-xl border-2 transition-all font-medium text-sm"
                        :class="selectedRole === 'student' ? 'border-blue-600 bg-blue-50 text-blue-600' : 'border-gray-100 text-gray-500 hover:border-gray-200'"
                        >
                            Student
                        </button>
                        <button 
                        @click="selectedRole = 'teacher'"
                        type="button"
                        class="py-2 px-4 rounded-xl border-2 transition-all font-medium text-sm"
                        :class="selectedRole === 'teacher' ? 'border-blue-600 bg-blue-50 text-blue-600' : 'border-gray-100 text-gray-500 hover:border-gray-200'"
                        >
                            Teacher
                        </button>
                    </div>
                    <p v-if="generalError" class="text-red-500 text-xs font-medium">{{ generalError }}</p>
                </div>
                <button @click="isLoginMode ? handleLogin() : handleRegister()"
                class="w-full py-3 bg-blue-500 text-white text-center font-bold rounded-lg hover:bg-blue-600 hover:-translate-y-1 transition-all duration-300"
                >
                    {{ isLoginMode ? 'Login' : 'Sign Up' }}
                </button>
                <p class="text-center text-sm text-gray-600 mt-2">
                    {{ isLoginMode ? "Don't have an account?" : "Already have an account?" }}
                    <button @click="toggleMode" class="text-blue-600 font-bold hover:underline ml-1">
                        {{ isLoginMode ? 'Register' : 'Login' }}
                    </button>
                </p>
            </div>
        </div>
    </div>
    <div 
    v-if="showSuccess" 
    class="fixed top-5 right-5 bg-green-500 text-white px-6 py-3 rounded-xl shadow-lg transition-all duration-300"
    >
        🎉 Вас вітає EduPlatform! Ви успішно зареєструвались
    </div>
</template>

<style scoped></style>
