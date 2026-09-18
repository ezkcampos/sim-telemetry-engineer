local M = {}

local function first(value)
  if type(value) == 'table' then return value[1] end
  return value
end

function M.new()
  local self = {
    config = nil,
    entries = {},
    error = nil,
  }
  setmetatable(self, { __index = M })
  self:reload()
  return self
end

function M:reload()
  self.entries = {}
  self.error = nil

  local ok, config = pcall(ac.INIConfig.carData, 0, 'setup.ini')
  if not ok or not config then
    self.error = 'Could not read car setup.ini'
    return
  end

  self.config = config
  for section, data in pairs(config.sections or {}) do
    local semanticID = first(data.ID)
    if semanticID then
      local entry = {
        id = tostring(semanticID),
        section = tostring(section),
        label = tostring(first(data.NAME) or first(data.LABEL) or semanticID),
        value = 0,
      }
      self.entries[entry.id] = entry
    end
  end
  self:refreshValues()
end

function M:refreshValues()
  for _, entry in pairs(self.entries) do
    local ok, value = pcall(ac.getSetupSpinnerValue, entry.section, entry.value or 0)
    if ok and value ~= nil then entry.value = tonumber(value) or value end
  end
end

function M:getEntries()
  return self.entries
end

function M:getValue(semanticID, defaultValue)
  local entry = self.entries[semanticID]
  if not entry or entry.value == nil then return defaultValue end
  return entry.value
end

return M
