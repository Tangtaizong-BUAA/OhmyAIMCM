-- Deterministic, text-preserving semantic environment mapping.
-- Only fenced Div wrappers change; their child blocks and inlines are untouched.
local environment_for_class = {
  assumption = "cumcmassumption",
  definition = "cumcmdefinition",
  theorem = "cumcmtheorem",
  lemma = "cumcmlemma",
  proposition = "cumcmproposition",
  proof = "cumcmproof",
  algorithm = "cumcmalgorithm",
  result = "cumcmresult",
  note = "cumcmnote",
  model = "cummodel"
}

local function declaration_blocks(meta)
  local state = pandoc.utils.stringify(meta["ai-usage-state"] or "")
  local summary = pandoc.utils.stringify(meta["ai-usage-summary"] or "")
  if state == "" then
    return {}
  end
  local message
  if state == "used" then
    message = "本论文使用了人工智能工具。用途摘要：" .. summary
      .. "。详细使用情况见支撑材料《AI工具使用详情.pdf》。"
  else
    message = "本论文未使用人工智能工具。"
  end
  return {
    pandoc.Header(1, {pandoc.Str("人工智能工具使用声明")},
      pandoc.Attr("ai-tool-usage-declaration", {"unnumbered"}, {})),
    pandoc.Para({pandoc.Str(message)})
  }
end

local function is_references_header(block)
  if block.t ~= "Header" then
    return false
  end
  local value = pandoc.utils.stringify(block.content):lower():gsub("%s+", "")
  return value == "参考文献" or value == "references" or value == "参考资料"
end

function Pandoc(doc)
  local keywords = pandoc.utils.stringify(doc.meta.keywords or "")
  if keywords ~= "" and doc.meta.abstract then
    local abstract_blocks = doc.meta.abstract
    table.insert(abstract_blocks, pandoc.RawBlock("latex", "\\begin{keywords}" .. keywords .. "\\end{keywords}"))
    doc.meta.abstract = pandoc.MetaBlocks(abstract_blocks)
  end
  local declaration = declaration_blocks(doc.meta)
  if #declaration == 0 then
    return doc
  end
  local output = {}
  local inserted = false
  for _, block in ipairs(doc.blocks) do
    if not inserted and is_references_header(block) then
      for _, declaration_block in ipairs(declaration) do
        table.insert(output, declaration_block)
      end
      inserted = true
    end
    table.insert(output, block)
  end
  if not inserted then
    for _, declaration_block in ipairs(declaration) do
      table.insert(output, declaration_block)
    end
  end
  doc.blocks = output
  doc.meta["ai-usage-state"] = nil
  doc.meta["ai-usage-summary"] = nil
  return doc
end

function Div(div)
  if FORMAT:match("latex") or FORMAT == "json" then
    for _, class_name in ipairs(div.classes) do
      local environment = environment_for_class[class_name]
      if environment then
        local blocks = {pandoc.RawBlock("latex", "\\begin{" .. environment .. "}")}
        for _, block in ipairs(div.content) do
          table.insert(blocks, block)
        end
        table.insert(blocks, pandoc.RawBlock("latex", "\\end{" .. environment .. "}"))
        return blocks
      end
    end
  end
  return div
end
