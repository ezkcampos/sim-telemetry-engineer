local M = {}

local function normalizedProgress(value)
  value = value % 1
  if value < 0 then value = value + 1 end
  return value
end

function M.new(sampleCount)
  local self = {
    sampleCount = sampleCount or 1000,
    points = {},
    minX = math.huge,
    maxX = -math.huge,
    minZ = math.huge,
    maxZ = -math.huge,
    ready = false,
  }
  setmetatable(self, { __index = M })
  self:sampleTrack()
  return self
end

function M:sampleTrack()
  if not ac.hasTrackSpline() then return end
  for i = 0, self.sampleCount do
    local progress = i / self.sampleCount
    local world = ac.trackProgressToWorldCoordinate(progress)
    if world then
      local point = { x = world.x, z = world.z, progress = progress }
      self.points[#self.points + 1] = point
      self.minX = math.min(self.minX, point.x)
      self.maxX = math.max(self.maxX, point.x)
      self.minZ = math.min(self.minZ, point.z)
      self.maxZ = math.max(self.maxZ, point.z)
    end
  end
  self.ready = #self.points > 2 and self.maxX > self.minX and self.maxZ > self.minZ
end

function M:worldPoint(progress)
  if not self.ready then return nil end
  progress = normalizedProgress(progress)
  local index = math.floor(progress * self.sampleCount) + 1
  return self.points[math.min(index, #self.points)]
end

function M:screenPoint(progress, topLeft, size)
  local point = self:worldPoint(progress)
  if not point then return topLeft end
  local padding = 18
  local worldWidth = math.max(1, self.maxX - self.minX)
  local worldHeight = math.max(1, self.maxZ - self.minZ)
  local scale = math.min(
    math.max(1, size.x - padding * 2) / worldWidth,
    math.max(1, size.y - padding * 2) / worldHeight
  )
  local drawnWidth = worldWidth * scale
  local drawnHeight = worldHeight * scale
  local offsetX = (size.x - drawnWidth) * 0.5
  local offsetY = (size.y - drawnHeight) * 0.5
  return vec2(
    topLeft.x + offsetX + (point.x - self.minX) * scale,
    topLeft.y + offsetY + (self.maxZ - point.z) * scale
  )
end

function M:drawRange(startProgress, endProgress, topLeft, size, color, width)
  startProgress = normalizedProgress(startProgress)
  endProgress = normalizedProgress(endProgress)
  if endProgress <= startProgress then endProgress = endProgress + 1 end
  local steps = math.max(2, math.ceil((endProgress - startProgress) * self.sampleCount))
  for i = 0, steps do
    local progress = startProgress + (endProgress - startProgress) * i / steps
    ui.pathLineTo(self:screenPoint(progress, topLeft, size))
  end
  ui.pathStroke(color, false, width)
end

function M:drawBase(topLeft, size, outlineColor, trackColor)
  self:drawRange(0, 0.999999, topLeft, size, outlineColor, 10)
  self:drawRange(0, 0.999999, topLeft, size, trackColor, 5)
end

function M:drawMarker(progress, topLeft, size, color)
  local center = self:screenPoint(progress, topLeft, size)
  ui.drawCircleFilled(center, 7, rgbm(0.01, 0.015, 0.02, 1), 20)
  ui.drawCircleFilled(center, 4.5, color, 20)
end

return M
