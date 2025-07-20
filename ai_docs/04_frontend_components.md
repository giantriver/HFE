# Frontend Components and Functionality Documentation

## Overview

This document describes the frontend architecture, components, and user interface functionality of the HFE Pose Analysis System built with Nuxt.js and Vue.js.

## Technology Stack

### Core Framework
- **Nuxt.js 3**: Full-stack Vue.js framework
- **Vue.js 3**: Progressive JavaScript framework with Composition API
- **TypeScript**: Type-safe JavaScript development

### UI Framework
- **PrimeVue**: Enterprise-class UI components
- **Tailwind CSS**: Utility-first CSS framework
- **PrimeIcons**: Icon library

### Development Tools
- **ESLint**: Code linting and formatting
- **Vite**: Fast build tool and dev server

## Project Structure

```
web/frontend/
├── pages/
│   └── index.vue           # Main pose analysis interface
├── nuxt.config.ts          # Nuxt configuration
├── package.json            # Dependencies and scripts
├── tailwind.config.js      # Tailwind CSS configuration
├── assets/
│   ├── css/
│   │   ├── global.css      # Global styles
│   │   └── tailwind.css    # Tailwind imports
│   └── images/             # Static images
└── public/
    └── favicon.ico         # Site favicon
```

## Main Component: index.vue

### Component Architecture

The main interface is a single-page component using Vue 3 Composition API:

```vue
<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

// Reactive state management
const selectedFile = ref(null)
const processing = ref(false)
const result = ref(null)
const error = ref(null)
const originalImageUrl = ref(null)
const enlargedImage = ref(null)
const showModal = ref(false)
const fileInput = ref(null)
</script>
```

### State Management

#### Reactive Variables

| Variable | Type | Purpose |
|----------|------|---------|
| `selectedFile` | File \| null | Currently selected image file |
| `processing` | boolean | Loading state during API call |
| `result` | PoseAnalysisResponse \| null | API response data |
| `error` | string \| null | Error message display |
| `originalImageUrl` | string \| null | Base64 URL of original image |
| `enlargedImage` | string \| null | URL of image in modal |
| `showModal` | boolean | Modal visibility state |
| `fileInput` | HTMLInputElement \| null | File input DOM reference |

#### State Transitions

```
Initial → File Selected → Processing → Results/Error
   ↓           ↓             ↓            ↓
[empty]   [preview]    [loading]   [comparison]
   ↑           ↑             ↑            ↑
   ←─── Reset ←──── Reset ←─── Reset ←────┘
```

### Core Functions

#### 1. File Selection Handler
```javascript
const handleFileSelect = (event) => {
  const file = event.target.files[0]
  if (file && file.type.startsWith('image/')) {
    selectedFile.value = file
    error.value = null
    
    // Create preview URL
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
```

#### 2. API Integration
```javascript
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

    const response = await $fetch('/api/v1/poseanalysisapi/analyze', {
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
```

#### 3. Image Enlargement Modal
```javascript
const enlargeImage = (imageUrl) => {
  enlargedImage.value = imageUrl
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
  enlargedImage.value = null
}

// Keyboard event handling
const handleKeydown = (event) => {
  if (event.key === 'Escape' && showModal.value) {
    closeModal()
  }
}
```

#### 4. Reset Functionality
```javascript
const reset = () => {
  selectedFile.value = null
  result.value = null
  error.value = null
  processing.value = false
  originalImageUrl.value = null
  closeModal()
  
  // Clear DOM file input
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}
```

### UI Layout Structure

#### 1. Upload Section
```vue
<div class="bg-white rounded-lg shadow-lg p-6 mb-6">
  <h2 class="text-xl font-semibold mb-4">Upload Image for Analysis</h2>
  
  <!-- File Input -->
  <input
    ref="fileInput"
    type="file"
    accept="image/*"
    class="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
    @change="handleFileSelect"
  >
  
  <!-- Action Buttons -->
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
</div>
```

#### 2. Original Image Preview
```vue
<!-- Only shown when file selected but no results yet -->
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
```

#### 3. Analysis Results
```vue
<div v-if="result" class="bg-white rounded-lg shadow-lg p-6">
  <h2 class="text-xl font-semibold mb-4">Analysis Results</h2>

  <div class="grid md:grid-cols-2 gap-6">
    <!-- Images Section (Vertical Layout) -->
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

    <!-- Data Panel -->
    <div>
      <!-- Best Score Display -->
      <!-- Left Arm Details -->
      <!-- Right Arm Details -->
    </div>
  </div>
</div>
```

#### 4. Enlargement Modal
```vue
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
```

## Styling and Design

### Design System

#### Color Palette
- **Primary**: Blue (`bg-blue-600`, `text-blue-700`)
- **Success**: Green (`text-green-600`)
- **Warning**: Yellow (`text-yellow-600`) 
- **Error**: Red (`text-red-600`)
- **Neutral**: Gray shades

#### Component Styling
- **Cards**: White background with rounded corners and shadows
- **Buttons**: Rounded with hover effects and disabled states
- **Images**: Rounded borders with hover transitions
- **Modal**: Dark overlay with centered content

### Responsive Design

#### Breakpoints
- **Mobile**: Default styles (< 768px)
- **Tablet**: `md:` prefix (≥ 768px)
- **Desktop**: `lg:` prefix (≥ 1024px)

#### Layout Adaptations
- **Mobile**: Single column, stacked elements
- **Tablet**: Two-column grid for results
- **Desktop**: Optimized spacing and sizing

## User Experience Features

### Loading States
- **File Input**: Immediate feedback on selection
- **Processing**: Spinner animation with text
- **Button States**: Disabled during processing

### Error Handling
- **File Validation**: Client-side type checking
- **API Errors**: User-friendly error messages
- **Visual Feedback**: Red error boxes

### Interactive Elements
- **Click to Enlarge**: Hover effects on images
- **Keyboard Navigation**: ESC key for modal
- **Visual Feedback**: Opacity changes on hover

### Accessibility
- **Alt Text**: Descriptive image alternatives
- **Keyboard Support**: ESC key, tab navigation
- **Color Contrast**: High contrast for readability
- **Screen Reader**: Semantic HTML structure

## Configuration

### Nuxt Configuration
```typescript
export default defineNuxtConfig({
  modules: [
    "@pinia/nuxt",
    "@nuxt/eslint", 
    "@nuxtjs/tailwindcss",
    "@primevue/nuxt-module",
    "@nuxtjs/i18n"
  ],
  
  nitro: {
    devProxy: {
      "/api": {
        target: "http://localhost:5008/api",
        changeOrigin: true
      }
    }
  }
})
```

### Development Scripts
```json
{
  "scripts": {
    "dev": "nuxt dev",
    "build": "nuxt build", 
    "preview": "nuxt preview",
    "lint": "eslint .",
    "lint:fix": "eslint . --fix"
  }
}
```

## Performance Considerations

### Optimization Techniques
- **Reactive State**: Minimal re-renders with ref()
- **Image Loading**: Base64 encoding for immediate display
- **Event Handling**: Efficient DOM manipulation
- **Memory Management**: Cleanup on component unmount

### Bundle Size
- **Tree Shaking**: Unused PrimeVue components excluded
- **Code Splitting**: Automatic route-based splitting
- **Image Optimization**: Client-side processing only

---
*Generated: 2025-01-20*
*Framework: Nuxt.js 3 + Vue.js 3*