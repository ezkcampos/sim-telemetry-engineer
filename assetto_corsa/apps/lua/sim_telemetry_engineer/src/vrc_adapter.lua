local M = {}

function M.new(carID)
  local self = {
    carID = carID,
    can = nil,
    connected = false,
    available = false,
    state = {},
  }
  setmetatable(self, { __index = M })

  local moduleName = string.format('content.cars.%s.extension.data_override.can', carID or '')
  local ok, can = pcall(require, moduleName)
  if ok and can then
    self.can = can
    self.available = true
  end
  return self
end

function M:update(dt)
  if not self.can then return end

  if not self.can.bus then
    if not self.connected then
      self.connected = true
      pcall(function() self.can:connect() end)
    end
    return
  end

  pcall(self.can.update, dt)
  local bus = self.can.bus
  local rawStrat = tonumber(bus.deploymentStrat)
  local rawSplit = tonumber(bus.deploymentSplit)
  self.state.strat = rawStrat and math.floor(rawStrat + 0.5) + 1 or nil
  self.state.split = rawSplit
  self.state.powerKW = tonumber(bus.rearMotorPowerKW)
  self.state.socMJ = tonumber(bus.kersChargeESOC)
end

function M:getState()
  return self.state
end

return M
