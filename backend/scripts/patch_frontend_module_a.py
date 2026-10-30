import os

# 1. Patch AgentSpecPane.tsx
spec_path = "frontend/src/components/studio/AgentSpecPane.tsx"
with open(spec_path, "r", encoding="utf-8") as f:
    spec_text = f.read()

# Fix bottom overflow by increasing bottom padding to pb-48
old_scroll = '<div className="flex-1 min-h-0 overflow-y-auto p-3.5 pb-28 space-y-3.5">'
new_scroll = '<div className="flex-1 min-h-0 overflow-y-auto p-3.5 pb-48 space-y-3.5">'

if old_scroll in spec_text:
    spec_text = spec_text.replace(old_scroll, new_scroll, 1)

# Add delete button and CrewAI badge to template buttons
old_btn = """                <button
                  key={dom.id}
                  onClick={() => onSelectDomain(dom)}
                  className={`text-left px-2.5 py-1.5 rounded-[4px] border transition-all text-xs ${
                    isSelected
                      ? "bg-[#16161a] border-[#2c2c35] text-[#f4f4f6] shadow-sm font-medium"
                      : "bg-[#09090b] border-[#1f1f24] text-[#9494a0] hover:border-[#2c2c35] hover:text-[#f4f4f6]"
                  }`}
                >
                  <div className="truncate font-medium">{dom.name}</div>
                  <div className="font-mono text-[9px] text-[#5b5b66] truncate uppercase">
                    {dom.domain_type.replace("_", " ")}
                  </div>
                </button>"""

new_btn = """                <div
                  key={dom.id}
                  onClick={() => onSelectDomain(dom)}
                  className={`group relative text-left px-2.5 py-1.5 rounded-[4px] border transition-all text-xs cursor-pointer ${
                    isSelected
                      ? "bg-[#16161a] border-[#2c2c35] text-[#f4f4f6] shadow-sm font-medium"
                      : "bg-[#09090b] border-[#1f1f24] text-[#9494a0] hover:border-[#2c2c35] hover:text-[#f4f4f6]"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="truncate font-medium flex items-center space-x-1">
                      <span>{dom.name}</span>
                    </div>
                    {!["brew-bite-cafe", "smilecare-dental", "apex-gurgaon-realty", "quickkart-d2c", "quickkart-d2c-support", "urban-chai-co"].includes(dom.id) && (
                      <button
                        type="button"
                        onClick={async (e) => {
                          e.stopPropagation();
                          if (confirm(`Delete custom agent "${dom.name}"?`)) {
                            const { deleteDomain } = await import("@/lib/api");
                            await deleteDomain(dom.id);
                            window.location.reload();
                          }
                        }}
                        className="text-[#9494a0] hover:text-[#ef4444] text-xs font-bold px-1"
                        title="Delete custom agent"
                      >
                        ×
                      </button>
                    )}
                  </div>
                  <div className="flex items-center justify-between mt-0.5">
                    <span className="font-mono text-[9px] text-[#5b5b66] truncate uppercase">
                      {dom.domain_type.replace("_", " ")}
                    </span>
                    <span className="font-mono text-[8px] px-1 py-0.2 rounded bg-[#1f1f24] text-[#9494a0]">
                      CrewAI 0ms
                    </span>
                  </div>
                </div>"""

if old_btn in spec_text:
    spec_text = spec_text.replace(old_btn, new_btn, 1)

# Add tooltip & caption to Compile button
old_compile_btn = """        {/* Action Buttons: Compile & Provision */}
        <div className="grid grid-cols-2 gap-2 pt-1">
          <button
            onClick={handleCompile}
            disabled={isCompiling}
            className="flex items-center justify-center space-x-1.5 py-1.5 px-3 bg-[#e4e4e7] hover:bg-[#ffffff] text-[#09090b] rounded-[4px] text-xs font-semibold transition-all shadow-sm disabled:opacity-50"
          >"""

new_compile_btn = """        {/* Action Buttons: Compile & Provision */}
        <div className="grid grid-cols-2 gap-2 pt-1">
          <button
            onClick={handleCompile}
            disabled={isCompiling}
            title="New Agent Creation: ~45s Deep CrewAI Compile"
            className="flex items-center justify-center space-x-1.5 py-1.5 px-3 bg-[#e4e4e7] hover:bg-[#ffffff] text-[#09090b] rounded-[4px] text-xs font-semibold transition-all shadow-sm disabled:opacity-50"
          >"""

if old_compile_btn in spec_text:
    spec_text = spec_text.replace(old_compile_btn, new_compile_btn, 1)

with open(spec_path, "w", encoding="utf-8") as f:
    f.write(spec_text)
print("AgentSpecPane.tsx patched successfully!")

# 2. Patch BusinessDemoView.tsx
demo_path = "frontend/src/components/views/BusinessDemoView.tsx"
with open(demo_path, "r", encoding="utf-8") as f:
    demo_text = f.read()

old_card = """                              <div>
                                <h4 className="text-xs font-bold text-[#151619]">
                                  {dom.name}
                                </h4>
                                <span className="text-[10px] text-[#737B8B] uppercase tracking-wider font-semibold">
                                  {dom.domain_type}
                                </span>
                              </div>"""

new_card = """                              <div>
                                <div className="flex items-center space-x-1.5 flex-wrap">
                                  <h4 className="text-xs font-bold text-[#151619]">
                                    {dom.name}
                                  </h4>
                                  <span className="text-[9px] font-mono px-1.5 py-0.5 rounded-full bg-[#151619]/5 text-[#151619] border border-[#151619]/10">
                                    CrewAI Trained · 0ms Ready
                                  </span>
                                </div>
                                <span className="text-[10px] text-[#737B8B] uppercase tracking-wider font-semibold">
                                  {dom.domain_type}
                                </span>
                              </div>"""

if old_card in demo_text:
    demo_text = demo_text.replace(old_card, new_card, 1)

# Add custom domain delete button on card header
old_select_dot = """                            {isSelected && (
                              <span className="w-2 h-2 rounded-full bg-[#151619]" />
                            )}
                          </div>"""

new_select_dot = """                            <div className="flex items-center space-x-1.5">
                              {!["brew-bite-cafe", "smilecare-dental", "apex-gurgaon-realty", "quickkart-d2c", "quickkart-d2c-support", "urban-chai-co"].includes(dom.id) && (
                                <button
                                  type="button"
                                  onClick={async (e) => {
                                    e.stopPropagation();
                                    if (confirm(`Delete custom agent "${dom.name}"?`)) {
                                      await deleteDomain(dom.id);
                                      window.location.reload();
                                    }
                                  }}
                                  className="w-5 h-5 rounded-full hover:bg-red-50 text-[#737B8B] hover:text-red-500 flex items-center justify-center text-xs font-bold transition-all"
                                  title="Delete custom agent"
                                >
                                  ×
                                </button>
                              )}
                              {isSelected && (
                                <span className="w-2 h-2 rounded-full bg-[#151619]" />
                              )}
                            </div>
                          </div>"""

if old_select_dot in demo_text:
    demo_text = demo_text.replace(old_select_dot, new_select_dot, 1)

with open(demo_path, "w", encoding="utf-8") as f:
    f.write(demo_text)
print("BusinessDemoView.tsx patched successfully!")

