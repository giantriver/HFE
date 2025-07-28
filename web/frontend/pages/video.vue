<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'

const selectedFile = ref(null)
const processing = ref(false)
const results = ref([])
const error = ref(null)
const originalVideoUrl = ref(null)
const enlargedImage = ref(null)
const showModal = ref(false)
const fileInput = ref(null)
const videoElement = ref(null)
const canvasElement = ref(null)
const progress = ref(0)
const totalFrames = ref(0)
const processedFrames = ref(0)
const generatingVideo = ref(false)
const mergedVideoUrl = ref(null)

// MediaPipe variables
let pose = null
let camera = null

const handleFileSelect = (event) => {
  const file = event.target.files[0]
  if (file && file.type.startsWith('video/')) {
    selectedFile.value = file
    error.value = null
    
    // Create URL for video preview
    const url = URL.createObjectURL(file)
    originalVideoUrl.value = url
  } else {
    error.value = 'Please select a valid video file'
    selectedFile.value = null
    originalVideoUrl.value = null
  }
}

const initializeMediaPipe = async () => {
  // Load MediaPipe scripts dynamically
  return new Promise((resolve, reject) => {
    if (window.Pose) {
      resolve()
      return
    }

    const scripts = [
      'https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js',
      'https://cdn.jsdelivr.net/npm/@mediapipe/control_utils/control_utils.js',
      'https://cdn.jsdelivr.net/npm/@mediapipe/drawing_utils/drawing_utils.js',
      'https://cdn.jsdelivr.net/npm/@mediapipe/pose/pose.js'
    ]

    let loadedScripts = 0
    
    scripts.forEach(src => {
      const script = document.createElement('script')
      script.src = src
      script.onload = () => {
        loadedScripts++
        if (loadedScripts === scripts.length) {
          resolve()
        }
      }
      script.onerror = reject
      document.head.appendChild(script)
    })
  })
}

const setupPose = () => {
  pose = new window.Pose({
    locateFile: (file) => {
      return `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${file}`
    }
  })

  pose.setOptions({
    modelComplexity: 1,
    smoothLandmarks: true,
    enableSegmentation: false,
    minDetectionConfidence: 0.5,
    minTrackingConfidence: 0.5
  })

  pose.onResults(onPoseResults)
}

const drawKeyLandmarksWithLabels = (ctx, landmarks, width, height) => {
  const keypoints = {
    "L_SH": 11, // LEFT_SHOULDER
    "L_EL": 13, // LEFT_ELBOW  
    "L_WR": 15, // LEFT_WRIST
    "L_HIP": 23, // LEFT_HIP
    "R_SH": 12, // RIGHT_SHOULDER
    "R_EL": 14, // RIGHT_ELBOW
    "R_WR": 16, // RIGHT_WRIST
    "R_HIP": 24  // RIGHT_HIP
  }

  ctx.font = Math.max(12, width / 50) + 'px Arial'
  ctx.fillStyle = '#FFFF00' // Yellow text
  ctx.strokeStyle = '#000000' // Black outline
  ctx.lineWidth = 2

  Object.entries(keypoints).forEach(([label, idx]) => {
    const landmark = landmarks[idx]
    const x = landmark.x * width
    const y = landmark.y * height
    const z = landmark.z

    const text = `${label} (${landmark.x.toFixed(2)}, ${landmark.y.toFixed(2)}, ${z.toFixed(2)})`
    
    // Draw text with outline
    ctx.strokeText(text, x + 5, y - 5)
    ctx.fillText(text, x + 5, y - 5)
    
    // Draw larger circle for key points
    ctx.beginPath()
    ctx.arc(x, y, Math.max(8, width / 100), 0, 2 * Math.PI)
    ctx.fillStyle = '#00FF00' // Green circle
    ctx.fill()
    ctx.strokeStyle = '#000000'
    ctx.lineWidth = 2
    ctx.stroke()
    ctx.fillStyle = '#FFFF00' // Reset text color
  })
}

const onPoseResults = (poseResults) => {
  const canvas = canvasElement.value
  const ctx = canvas.getContext('2d')
  const video = videoElement.value
  
  // Clear canvas
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  
  // Draw the video frame first
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
  
  if (poseResults.poseLandmarks) {
    // Draw pose landmarks and connections on top of the video frame
    window.drawConnectors(ctx, poseResults.poseLandmarks, window.POSE_CONNECTIONS, {color: '#00FF00', lineWidth: 4})
    window.drawLandmarks(ctx, poseResults.poseLandmarks, {color: '#FF0000', lineWidth: 2})
    
    // Draw key landmarks with labels
    drawKeyLandmarksWithLabels(ctx, poseResults.poseLandmarks, canvas.width, canvas.height)
    
    // Calculate angles
    const angleData = calculateAngles(poseResults.poseLandmarks)
    
    // Save frame result
    const frameData = {
      timestamp: videoElement.value.currentTime,
      landmarks: poseResults.poseLandmarks,
      angles: angleData,
      imageData: canvas.toDataURL('image/png')
    }
    
    results.value.push(frameData)
  }
  
  processedFrames.value++
  progress.value = (processedFrames.value / totalFrames.value) * 100
}

const calculateAngles = (landmarks) => {
  // Convert landmarks to arrays for easier calculation
  const lm = landmarks.map(landmark => ({
    x: landmark.x,
    y: landmark.y,
    z: landmark.z
  }))

  // MediaPipe pose landmark indices
  const POSE_LANDMARKS = {
    LEFT_SHOULDER: 11,
    LEFT_ELBOW: 13,
    LEFT_WRIST: 15,
    LEFT_HIP: 23,
    RIGHT_SHOULDER: 12,
    RIGHT_ELBOW: 14,
    RIGHT_WRIST: 16,
    RIGHT_HIP: 24
  }

  const calculateArmAngles = (side) => {
    const shoulderIdx = side === 'LEFT' ? POSE_LANDMARKS.LEFT_SHOULDER : POSE_LANDMARKS.RIGHT_SHOULDER
    const elbowIdx = side === 'LEFT' ? POSE_LANDMARKS.LEFT_ELBOW : POSE_LANDMARKS.RIGHT_ELBOW
    const wristIdx = side === 'LEFT' ? POSE_LANDMARKS.LEFT_WRIST : POSE_LANDMARKS.RIGHT_WRIST
    const hipIdx = side === 'LEFT' ? POSE_LANDMARKS.LEFT_HIP : POSE_LANDMARKS.RIGHT_HIP

    const shoulder = lm[shoulderIdx]
    const elbow = lm[elbowIdx]
    const wrist = lm[wristIdx]
    const hip = lm[hipIdx]

    // Calculate vectors
    const shoulderToElbow = {
      x: elbow.x - shoulder.x,
      y: elbow.y - shoulder.y,
      z: elbow.z - shoulder.z
    }
    
    const shoulderToHip = {
      x: hip.x - shoulder.x,
      y: hip.y - shoulder.y,
      z: hip.z - shoulder.z
    }
    
    const elbowToWrist = {
      x: wrist.x - elbow.x,
      y: wrist.y - elbow.y,
      z: wrist.z - elbow.z
    }
    
    const elbowToShoulder = {
      x: shoulder.x - elbow.x,
      y: shoulder.y - elbow.y,
      z: shoulder.z - elbow.z
    }

    // Calculate angles
    const raiseAngle = angleBetween(shoulderToElbow, shoulderToHip)
    const elbowAngle = angleBetween(elbowToWrist, elbowToShoulder)

    return { raiseAngle, elbowAngle }
  }

  const leftArm = calculateArmAngles('LEFT')
  const rightArm = calculateArmAngles('RIGHT')

  return {
    leftArm,
    rightArm
  }
}

const angleBetween = (v1, v2) => {
  const dot = v1.x * v2.x + v1.y * v2.y + v1.z * v2.z
  const norm1 = Math.sqrt(v1.x * v1.x + v1.y * v1.y + v1.z * v1.z)
  const norm2 = Math.sqrt(v2.x * v2.x + v2.y * v2.y + v2.z * v2.z)
  
  if (norm1 === 0 || norm2 === 0) return 0
  
  const cos = Math.max(-1, Math.min(1, dot / (norm1 * norm2)))
  return Math.acos(cos) * (180 / Math.PI)
}

const processVideoFrames = async () => {
  if (!selectedFile.value) {
    error.value = 'Please select a video first'
    return
  }

  processing.value = true
  error.value = null
  results.value = []
  processedFrames.value = 0
  progress.value = 0

  try {
    await initializeMediaPipe()
    setupPose()
    
    await nextTick()
    
    const video = videoElement.value
    const canvas = canvasElement.value
    
    // Set up video
    video.src = originalVideoUrl.value
    
    return new Promise((resolve, reject) => {
      video.onloadedmetadata = () => {
        canvas.width = video.videoWidth
        canvas.height = video.videoHeight
        
        // Calculate total frames (approximate)
        const fps = 30 // Assume 30 fps, could be made dynamic
        totalFrames.value = Math.floor(video.duration * fps)
        
        video.currentTime = 0
        processFrame()
      }
      
      const processFrame = async () => {
        if (video.currentTime >= video.duration) {
          processing.value = false
          resolve()
          return
        }
        
        // Send frame to MediaPipe
        await pose.send({ image: video })
        
        // Move to next frame (process every 0.1 seconds)
        video.currentTime += 0.1
        
        // Use requestAnimationFrame for smoother processing
        requestAnimationFrame(processFrame)
      }
      
      video.onerror = reject
    })
    
  } catch (err) {
    error.value = 'Error processing video. Please try again.'
    console.error(err)
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
  results.value = []
  error.value = null
  processing.value = false
  originalVideoUrl.value = null
  progress.value = 0
  totalFrames.value = 0
  processedFrames.value = 0
  generatingVideo.value = false
  
  // Clean up video URLs
  if (mergedVideoUrl.value) {
    URL.revokeObjectURL(mergedVideoUrl.value)
    mergedVideoUrl.value = null
  }
  
  closeModal()
  
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

const downloadResults = () => {
  const dataStr = JSON.stringify(results.value, null, 2)
  const dataBlob = new Blob([dataStr], {type: 'application/json'})
  const url = URL.createObjectURL(dataBlob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'pose_analysis_results.json'
  link.click()
  URL.revokeObjectURL(url)
}

const downloadMergedVideo = () => {
  if (!mergedVideoUrl.value) return
  
  const link = document.createElement('a')
  link.href = mergedVideoUrl.value
  link.download = 'pose_analysis_video.webm'
  link.click()
}

const generateMergedVideo = async () => {
  if (results.value.length === 0) return

  generatingVideo.value = true

  try {
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    
    // Set canvas size based on first frame
    const firstFrame = new Image()
    firstFrame.src = results.value[0].imageData
    
    return new Promise((resolve) => {
      firstFrame.onload = async () => {
        canvas.width = firstFrame.width
        canvas.height = firstFrame.height

        // Create MediaRecorder to record canvas
        const stream = canvas.captureStream(30) // 30 FPS
        const mediaRecorder = new MediaRecorder(stream, {
          mimeType: 'video/webm;codecs=vp9'
        })
        
        const chunks = []
        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            chunks.push(event.data)
          }
        }

        mediaRecorder.onstop = () => {
          const blob = new Blob(chunks, { type: 'video/webm' })
          const url = URL.createObjectURL(blob)
          
          // Store URL for video player
          mergedVideoUrl.value = url
          
          generatingVideo.value = false
          resolve()
        }

        mediaRecorder.start()

        // Draw each frame with a delay
        let frameIndex = 0
        const drawFrame = () => {
          if (frameIndex >= results.value.length) {
            mediaRecorder.stop()
            return
          }

          const img = new Image()
          img.src = results.value[frameIndex].imageData
          img.onload = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height)
            ctx.drawImage(img, 0, 0)
            
            frameIndex++
            // Draw next frame after delay (approximately 100ms per frame for 10fps)
            setTimeout(drawFrame, 100)
          }
        }

        drawFrame()
      }
    })
  } catch (error) {
    generatingVideo.value = false
    error.value = 'Error generating merged video'
    console.error(error)
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  if (originalVideoUrl.value) {
    URL.revokeObjectURL(originalVideoUrl.value)
  }
  if (mergedVideoUrl.value) {
    URL.revokeObjectURL(mergedVideoUrl.value)
  }
})
</script>

<template>
  <div class="container mx-auto p-6 max-w-6xl">
    <h1 class="text-3xl font-bold text-center mb-8">Video Pose Analysis Tool</h1>

    <!-- Upload Section -->
    <div class="bg-white rounded-lg shadow-lg p-6 mb-6">
      <h2 class="text-xl font-semibold mb-4">Upload Video for Analysis</h2>

      <div class="mb-4">
        <input
          ref="fileInput"
          type="file"
          accept="video/*"
          class="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
          @change="handleFileSelect"
        >
      </div>

      <div class="flex gap-4">
        <button
          :disabled="!selectedFile || processing"
          class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          @click="processVideoFrames"
        >
          {{ processing ? 'Processing...' : 'Analyze Video' }}
        </button>

        <button
          class="px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
          @click="reset"
        >
          Reset
        </button>

        <button
          v-if="results.length > 0"
          class="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
          @click="downloadResults"
        >
          Download Results
        </button>

        <button
          v-if="results.length > 0"
          :disabled="generatingVideo"
          class="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
          @click="generateMergedVideo"
        >
          {{ generatingVideo ? 'Generating Video...' : 'Generate Merged Video' }}
        </button>

        <button
          v-if="mergedVideoUrl"
          class="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
          @click="downloadMergedVideo"
        >
          Download Video
        </button>
      </div>

      <!-- Error Display -->
      <div v-if="error" class="mt-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
        {{ error }}
      </div>

      <!-- Progress Bar -->
      <div v-if="processing" class="mt-4">
        <div class="flex justify-between text-sm text-gray-600 mb-1">
          <span>Processing frames...</span>
          <span>{{ processedFrames }}/{{ totalFrames }} ({{ Math.round(progress) }}%)</span>
        </div>
        <div class="w-full bg-gray-200 rounded-full h-2">
          <div 
            class="bg-blue-600 h-2 rounded-full transition-all duration-300"
            :style="{ width: progress + '%' }"
          />
        </div>
      </div>
    </div>

    <!-- Video Preview -->
    <div v-if="originalVideoUrl && !processing" class="bg-white rounded-lg shadow-lg p-6 mb-6">
      <h2 class="text-xl font-semibold mb-4">Video Preview</h2>
      <div class="flex justify-center">
        <video
          :src="originalVideoUrl"
          controls
          class="max-w-md w-full rounded-lg border"
        />
      </div>
    </div>

    <!-- Hidden elements for processing -->
    <div class="hidden">
      <video ref="videoElement" />
      <canvas ref="canvasElement" />
    </div>

    <!-- Results Section -->
    <div v-if="results.length > 0" class="bg-white rounded-lg shadow-lg p-6">
      <h2 class="text-xl font-semibold mb-4">Analysis Results ({{ results.length }} frames processed)</h2>

      <!-- Results Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="(result, index) in results"
          :key="index"
          class="border rounded-lg p-4 hover:shadow-md transition-shadow"
        >
          <div class="mb-2">
            <h3 class="font-semibold text-sm">Frame {{ index + 1 }}</h3>
            <p class="text-xs text-gray-600">Time: {{ result.timestamp.toFixed(2) }}s</p>
          </div>
          
          <img
            :src="result.imageData"
            :alt="`Frame ${index + 1}`"
            class="w-full h-32 object-cover rounded cursor-pointer hover:opacity-80 transition-opacity mb-2"
            @click="enlargeImage(result.imageData)"
          >
          
          <div class="text-xs space-y-1">
            <div class="flex justify-between">
              <span>Left Raise:</span>
              <span>{{ result.angles.leftArm.raiseAngle.toFixed(1) }}°</span>
            </div>
            <div class="flex justify-between">
              <span>Left Elbow:</span>
              <span>{{ result.angles.leftArm.elbowAngle.toFixed(1) }}°</span>
            </div>
            <div class="flex justify-between">
              <span>Right Raise:</span>
              <span>{{ result.angles.rightArm.raiseAngle.toFixed(1) }}°</span>
            </div>
            <div class="flex justify-between">
              <span>Right Elbow:</span>
              <span>{{ result.angles.rightArm.elbowAngle.toFixed(1) }}°</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Merged Video Player -->
    <div v-if="mergedVideoUrl" class="bg-white rounded-lg shadow-lg p-6 mt-6">
      <h2 class="text-xl font-semibold mb-4">Merged Video with Pose Analysis</h2>
      <div class="flex justify-center">
        <video
          :src="mergedVideoUrl"
          controls
          autoplay
          loop
          class="max-w-full w-full max-h-[600px] rounded-lg border shadow-md"
        >
          Your browser does not support the video tag.
        </video>
      </div>
      <p class="text-sm text-gray-600 mt-2 text-center">
        This video shows all processed frames with pose landmarks and angle calculations overlaid.
      </p>
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
            alt="Enlarged frame"
            class="max-w-full max-h-[80vh] object-contain rounded"
          >
        </div>
      </div>
    </div>
  </div>
</template>