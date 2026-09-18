local SetupReader = require('src/setup_reader')
local DeploymentModel = require('src/deployment_model')
local TrackMap = require('src/track_map')
local VrcAdapter = require('src/vrc_adapter')

local storage = ac.storage({
  selectedStrat = 1,
  followLiveStrat = true,
  showDiagnostics = false,
})

local state = {
  carID = nil,
  trackID = nil,
  setup = nil,
  model = nil,
  trackMap = nil,
  vrc = nil,
  refreshTimer = 0,
  status = 'Waiting for session',
}

local colors = {
  baseOutline = rgbm(0.02, 0.025, 0.035, 1),
  baseTrack = rgbm(0.26, 0.28, 0.33, 1),
  deploy = rgbm(0.17, 0.82, 0.42, 1),
  clipping = rgbm(1.00, 0.67, 0.12, 1),
  superclip = rgbm(0.95, 0.20, 0.24, 1),
  car = rgbm(0.20, 0.70, 1.00, 1),
  textMuted = rgbm(0.65, 0.68, 0.74, 1),
}

local function clamp(value, minimum, maximum)
  return math.max(minimum, math.min(maximum, value))
end

local function initialize()
  state.carID = ac.getCarID(0)
  state.trackID = ac.getTrackID()
  state.setup = SetupReader.new()
  state.model = DeploymentModel.build(state.setup)
  state.trackMap = TrackMap.new(1200)
  state.vrc = VrcAdapter.new(state.carID)

  if not ac.hasTrackSpline() then
    state.status = 'This track does not expose a CSP spline'
  elseif not state.trackMap.ready then
    state.status = 'Could not sample the track spline'
  elseif state.model.stratCount == 0 then
    state.status = 'No deployment strategy IDs found in setup.ini'
  else
    state.status = 'Read-only live map ready'
    storage.selectedStrat = clamp(storage.selectedStrat, 1, state.model.stratCount)
  end
end

local function needsReinitialize()
  return state.carID ~= ac.getCarID(0) or state.trackID ~= ac.getTrackID()
end

local function selectedStrat()
  local live = state.vrc and state.vrc:getState() or nil
  if storage.followLiveStrat and live and live.strat then
    return clamp(live.strat, 1, math.max(1, state.model.stratCount))
  end
  return clamp(storage.selectedStrat, 1, math.max(1, state.model.stratCount))
end

local function refreshSetupModel()
  if not state.setup then return end
  state.setup:refreshValues()
  state.model = DeploymentModel.build(state.setup)
  storage.selectedStrat = clamp(storage.selectedStrat, 1, math.max(1, state.model.stratCount))
end

local function legendItem(label, color)
  local cursor = ui.getCursor()
  ui.drawRectFilled(cursor + vec2(0, 4), cursor + vec2(18, 8), color, 2)
  ui.setCursor(cursor + vec2(24, 0))
  ui.text(label)
end

local function copyDiagnostics()
  local report = {
    'Sim Telemetry Engineer diagnostics',
    'Car: ' .. tostring(state.carID),
    'Track: ' .. tostring(state.trackID),
    'Status: ' .. tostring(state.status),
    'Strategies: ' .. tostring(state.model and state.model.stratCount or 0),
    '',
    state.model and state.model:diagnosticsText() or 'No model',
  }
  ui.setClipboardText(table.concat(report, '\n'))
end

function script.update(dt)
  if not state.carID or needsReinitialize() then
    initialize()
  end

  if state.vrc then state.vrc:update(dt) end
  state.refreshTimer = state.refreshTimer + dt
  if state.refreshTimer >= 0.25 then
    state.refreshTimer = 0
    refreshSetupModel()
  end
end

function script.main(dt)
  if not state.carID then initialize() end

  local sim = ac.getSim()
  local car = ac.getCar(0)
  local live = state.vrc and state.vrc:getState() or nil
  local strat = selectedStrat()
  local zones = state.model and state.model:getZones(strat) or {}
  local trackLength = sim.trackLengthM or 0
  local distance = car and car.splinePosition and car.splinePosition * trackLength or 0

  ui.text('LIVE DEPLOYMENT MAP')
  ui.sameLine(0, 16)
  ui.textColored(state.status, colors.textMuted)
  ui.separator()

  local splitText = live and live.split and string.format('%.0f', live.split) or '—'
  ui.text(string.format('STRAT %d   SPLIT %s   %.0f m', strat, splitText, distance))

  local soc = live and live.socMJ or nil
  local power = live and live.powerKW or nil
  if soc or power then
    ui.text(string.format('SoC %s MJ   Rear motor %s kW',
      soc and string.format('%.2f', soc) or '—',
      power and string.format('%.0f', power) or '—'))
  elseif car and car.kersCharge then
    local displayedSoc = car.kersCharge <= 1.01 and car.kersCharge * 100 or car.kersCharge
    ui.text(string.format('KERS charge %.1f%%', displayedSoc))
  end

  local topLeft = ui.getCursor() + vec2(0, 8)
  local available = ui.availableSpace()
  local mapHeight = math.max(230, available.y - 122)
  local mapSize = vec2(available.x, mapHeight)
  ui.drawRectFilled(topLeft, topLeft + mapSize, rgbm(0.035, 0.04, 0.055, 0.88), 8)

  if state.trackMap and state.trackMap.ready then
    state.trackMap:drawBase(topLeft, mapSize, colors.baseOutline, colors.baseTrack)
    for _, zone in ipairs(zones) do
      state.trackMap:drawRange(
        zone.startM / math.max(trackLength, 1),
        zone.endM / math.max(trackLength, 1),
        topLeft,
        mapSize,
        colors[zone.kind] or colors.deploy,
        5
      )
    end
    if car then
      state.trackMap:drawMarker(car.splinePosition or 0, topLeft, mapSize, colors.car)
    end
  else
    ui.drawText(state.status, topLeft + vec2(16, 16), colors.textMuted)
  end
  ui.setCursor(topLeft + vec2(0, mapHeight + 8))

  legendItem('Deploy', colors.deploy)
  ui.sameLine(0, 18)
  legendItem('Clipping', colors.clipping)
  ui.sameLine(0, 18)
  legendItem('Super-clipping', colors.superclip)

  if ui.button('◀') then
    storage.followLiveStrat = false
    storage.selectedStrat = clamp(strat - 1, 1, math.max(1, state.model.stratCount))
  end
  ui.sameLine()
  if ui.button(storage.followLiveStrat and 'LIVE' or 'MANUAL') then
    storage.followLiveStrat = not storage.followLiveStrat
  end
  ui.sameLine()
  if ui.button('▶') then
    storage.followLiveStrat = false
    storage.selectedStrat = clamp(strat + 1, 1, math.max(1, state.model.stratCount))
  end
  ui.sameLine(0, 16)
  ui.text(string.format('%d zone(s)', #zones))

  if state.model and #state.model.unmatched > 0 then
    ui.sameLine(0, 16)
    if ui.button('Diagnostics') then storage.showDiagnostics = not storage.showDiagnostics end
  end

  if storage.showDiagnostics and state.model then
    ui.separator()
    ui.textWrapped(state.model:diagnosticsText())
    if ui.button('Copy diagnostics') then copyDiagnostics() end
  end
end

function script.settings(dt)
  ui.text('Sim Telemetry Engineer')
  ui.separator()
  ui.textWrapped('The app only reads the current setup and live telemetry. It never writes to the car setup.')
  if ui.checkbox('Follow live VRC strategy', storage.followLiveStrat) then
    storage.followLiveStrat = not storage.followLiveStrat
  end
  if state.model then
    ui.text(string.format('Detected strategies: %d', state.model.stratCount))
    ui.text(string.format('Unmatched energy IDs: %d', #state.model.unmatched))
  end
  if ui.button('Copy diagnostics') then copyDiagnostics() end
end
