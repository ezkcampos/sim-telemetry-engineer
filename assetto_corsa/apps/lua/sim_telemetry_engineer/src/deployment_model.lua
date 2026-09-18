local M = {}

local function contains(value, token)
  return string.find(value, token, 1, true) ~= nil
end

local function energyRelated(id)
  return contains(id, 'STRAT') or contains(id, 'DEPLOY') or contains(id, 'CLIP')
    or contains(id, 'SPLIT') or contains(id, 'SUPER') or contains(id, 'ERS')
end

local function ensureSplit(strategies, stratNumber, splitNumber)
  strategies[stratNumber] = strategies[stratNumber] or {}
  strategies[stratNumber][splitNumber] = strategies[stratNumber][splitNumber] or {
    number = splitNumber,
  }
  return strategies[stratNumber][splitNumber]
end

local function classify(id)
  local strat, split = id:match('^STRAT_(%d+)_HK_DEPLOYMENT_(%d+)_START$')
  if strat then return tonumber(strat), tonumber(split), 'deployStart' end
  strat, split = id:match('^STRAT_(%d+)_H_DEPLOYMENT_(%d+)_END$')
  if strat then return tonumber(strat), tonumber(split), 'hybridEnd' end
  strat, split = id:match('^STRAT_(%d+)_K_DEPLOYMENT_(%d+)_END$')
  if strat then return tonumber(strat), tonumber(split), 'deployEnd' end

  strat = id:match('STRAT_?(%d+)')
  split = id:match('SPLIT_?(%d+)') or id:match('DEPLOYMENT_(%d+)')
  if not strat or not split then return nil end

  local field = nil
  if contains(id, 'SUPER') and contains(id, 'START') then field = 'superStart'
  elseif contains(id, 'SUPER') and (contains(id, 'END') or contains(id, 'STOP')) then field = 'superEnd'
  elseif contains(id, 'CLIP') and contains(id, 'START') then field = 'clipStart'
  elseif contains(id, 'CLIP') and (contains(id, 'END') or contains(id, 'STOP')) then field = 'clipEnd'
  elseif contains(id, 'DEPLOY') and contains(id, 'START') then field = 'deployStart'
  elseif contains(id, 'DEPLOY') and (contains(id, 'END') or contains(id, 'STOP')) then field = 'deployEnd'
  end

  if not field then return nil end
  return tonumber(strat), tonumber(split), field
end

local function addZone(zones, kind, startM, endM, split)
  startM = tonumber(startM)
  endM = tonumber(endM)
  if not startM or not endM or startM == endM then return end
  zones[#zones + 1] = {
    kind = kind,
    startM = startM,
    endM = endM,
    split = split,
  }
end

function M.build(reader)
  local self = {
    strategies = {},
    stratCount = 0,
    unmatched = {},
  }
  setmetatable(self, { __index = M })

  for id, entry in pairs(reader:getEntries()) do
    local upperID = string.upper(id)
    local strat, split, field = classify(upperID)
    if strat and split and field then
      local item = ensureSplit(self.strategies, strat, split)
      item[field] = entry.value
      item[field .. 'ID'] = id
      self.stratCount = math.max(self.stratCount, strat)
    elseif energyRelated(upperID) then
      self.unmatched[#self.unmatched + 1] = id
      local detectedStrat = tonumber(upperID:match('STRAT_?(%d+)'))
      if detectedStrat then self.stratCount = math.max(self.stratCount, detectedStrat) end
    end
  end

  table.sort(self.unmatched)
  return self
end

function M:getZones(stratNumber)
  local zones = {}
  local splits = self.strategies[stratNumber] or {}
  local ordered = {}
  for _, split in pairs(splits) do ordered[#ordered + 1] = split end
  table.sort(ordered, function(a, b) return a.number < b.number end)

  for _, split in ipairs(ordered) do
    addZone(zones, 'deploy', split.deployStart, split.deployEnd, split.number)
    addZone(zones, 'clipping', split.clipStart, split.clipEnd, split.number)
    addZone(zones, 'superclip', split.superStart, split.superEnd, split.number)
  end
  return zones
end

function M:diagnosticsText()
  local lines = {
    string.format('Recognized strategy count: %d', self.stratCount),
    string.format('Unmatched energy-related IDs: %d', #self.unmatched),
  }
  for _, id in ipairs(self.unmatched) do lines[#lines + 1] = '- ' .. id end
  return table.concat(lines, '\n')
end

return M
