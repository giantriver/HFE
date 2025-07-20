<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const config = useRuntimeConfig()

const selectedFile = ref(null)
const processing = ref(false)
const result = ref(null)
const error = ref(null)
const originalImageUrl = ref(null)
const enlargedImage = ref(null)
const showModal = ref(false)
const fileInput = ref(null)

const handleFileSelect = (event) => {
  const file = event.target.files[0]
  if (file && file.type.startsWith('image/')) {
    selectedFile.value = file
    error.value = null
    
    // Create URL for original image preview
    const reader = new FileReader()
    reader.onload = (e) => {
      originalImageUrl.value = e.target.result
    }
    reader.readAsDataURL(file)
  } else {
    error.value = 'Please select a valid image file'
    selectedFile.value = null
    originalImageUrl.value = null
  }
}

const uploadAndAnalyze = async () => {
  if (!selectedFile.value) {
    error.value = 'Please select an image first'
    return
  }

  processing.value = true
  error.value = null
  result.value = null

  try {
    const formData = new FormData()
    formData.append('image', selectedFile.value)

    const baseURL = config.public.apiBase
    const response = await $fetch(`${baseURL}/poseanalysisapi/analyze`, {
      method: 'POST',
      body: formData
    })

    result.value = response
  } catch (err) {
    error.value = err.data?.message || 'Error processing image. Please try again.'
  } finally {
    processing.value = false
  }
}

const enlargeImage = (imageUrl) => {
  enlargedImage.value = imageUrl
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
  enlargedImage.value = null
}

const handleKeydown = (event) => {
  if (event.key === 'Escape' && showModal.value) {
    closeModal()
  }
}

const reset = () => {
  selectedFile.value = null
  result.value = null
  error.value = null
  processing.value = false
  originalImageUrl.value = null
  closeModal()
  
  // Clear the file input element
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <div class="container mx-auto p-6 max-w-4xl">
    <h1 class="text-3xl font-bold text-center mb-8">Pose Analysis Tool</h1>

    <!-- Upload Section -->
    <div class="bg-white rounded-lg shadow-lg p-6 mb-6">
      <h2 class="text-xl font-semibold mb-4">Upload Image for Analysis</h2>

      <div class="mb-4">
        <input
          ref="fileInput"
          type="file"
          accept="image/*"
          class="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
          @change="handleFileSelect"
        >
      </div>

      <div class="flex gap-4">
        <button
          :disabled="!selectedFile || processing"
          class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          @click="uploadAndAnalyze"
        >
          {{ processing ? 'Processing...' : 'Analyze Pose' }}
        </button>

        <button
          class="px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
          @click="reset"
        >
          Reset
        </button>
      </div>

      <!-- Error Display -->
      <div v-if="error" class="mt-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
        {{ error }}
      </div>

      <!-- Loading Indicator -->
      <div v-if="processing" class="mt-4 text-center">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        <p class="mt-2 text-gray-600">
          Analyzing pose...
        </p>
      </div>
    </div>

    <!-- Original Image Preview (only show when no results) -->
    <div v-if="originalImageUrl && !result" class="bg-white rounded-lg shadow-lg p-6 mb-6">
      <h2 class="text-xl font-semibold mb-4">Original Image</h2>
      <div class="flex justify-center">
        <img
          :src="originalImageUrl"
          alt="Original uploaded image"
          class="max-w-md w-full rounded-lg border"
        >
      </div>
    </div>

    <!-- Results Section -->
    <div v-if="result" class="bg-white rounded-lg shadow-lg p-6">
      <h2 class="text-xl font-semibold mb-4">Analysis Results</h2>

      <div class="grid md:grid-cols-2 gap-6">
        <!-- Images Section -->
        <div class="space-y-6">
          <!-- Original Image -->
          <div>
            <h3 class="text-lg font-medium mb-2">Original Image</h3>
            <img
              :src="originalImageUrl"
              alt="Original uploaded image"
              class="w-full rounded-lg border cursor-pointer hover:opacity-80 transition-opacity"
              @click="enlargeImage(originalImageUrl)"
            >
          </div>
          
          <!-- Processed Image -->
          <div>
            <h3 class="text-lg font-medium mb-2">Processed Image</h3>
            <img
              :src="result.processed_image"
              alt="Processed pose analysis"
              class="w-full rounded-lg border cursor-pointer hover:opacity-80 transition-opacity"
              @click="enlargeImage(result.processed_image)"
            >
          </div>
        </div>

        <!-- Scores and Data -->
        <div>
          <h3 class="text-lg font-medium mb-4">Pose Analysis Data</h3>

          <!-- Best Score -->
          <div class="bg-gray-50 rounded-lg p-4 mb-4">
            <h4 class="font-semibold text-green-700">Best Side: {{ result.best_side }}</h4>
            <p class="text-sm text-gray-600 mt-1">{{ result.best_score.desc }}</p>
            <div class="mt-2">
              <span
                class="text-2xl font-bold"
                :class="{
                  'text-green-600': result.best_score.score >= 7,
                  'text-yellow-600': result.best_score.score >= 4 && result.best_score.score < 7,
                  'text-red-600': result.best_score.score < 4
                }"
              >
                Score: {{ result.best_score.score }}/10
              </span>
            </div>
          </div>

          <!-- Left Arm Details -->
          <div class="border rounded-lg p-4 mb-3">
            <h4 class="font-semibold text-blue-700">Left Arm</h4>
            <div class="text-sm mt-2 space-y-1">
              <p><strong>Raise Angle:</strong> {{ result.left_arm.theta_raise.toFixed(1) }}°</p>
              <p><strong>Elbow Angle:</strong> {{ result.left_arm.theta_elbow.toFixed(1) }}°</p>
              <p><strong>Description:</strong> {{ result.left_arm.desc }}</p>
              <p><strong>Score:</strong> {{ result.left_arm.score }}/10</p>
            </div>
          </div>

          <!-- Right Arm Details -->
          <div class="border rounded-lg p-4">
            <h4 class="font-semibold text-red-700">Right Arm</h4>
            <div class="text-sm mt-2 space-y-1">
              <p><strong>Raise Angle:</strong> {{ result.right_arm.theta_raise.toFixed(1) }}°</p>
              <p><strong>Elbow Angle:</strong> {{ result.right_arm.theta_elbow.toFixed(1) }}°</p>
              <p><strong>Description:</strong> {{ result.right_arm.desc }}</p>
              <p><strong>Score:</strong> {{ result.right_arm.score }}/10</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Image Enlargement Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50" @click="closeModal">
      <div class="max-w-[90vw] max-h-[90vh] p-4">
        <div class="relative bg-white rounded-lg p-4">
          <button
            class="absolute top-2 right-2 text-gray-500 hover:text-gray-700 text-2xl font-bold"
            @click="closeModal"
          >
            ×
          </button>
          <img
            :src="enlargedImage"
            alt="Enlarged image"
            class="max-w-full max-h-[80vh] object-contain rounded"
          >
        </div>
      </div>
    </div>
  </div>
</template>