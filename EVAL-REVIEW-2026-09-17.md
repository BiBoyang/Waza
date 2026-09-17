# Waza Skill 审查报告（skill-up 评测）

- 日期：2026-09-17
- 对象：`/Users/boyang/code/Waza`（tw93/Waza，8 skills），commit `7c4baac`
- 方法：skill-up 声明式评测，kimi custom engine（本机 kimi CLI），每 skill 2-3 个用例，with_skill / without_skill 对照，agent_judge（kimi）+ expect/rule_based
- 覆盖：8 个 skill 全部完成首轮（ui 由后续会话补跑，iteration-4 完整结果，引擎同为 k3）
- 评测产物：`skills/*/evals/`（用例）+ `skills/*-workspace/`（报告）+ `evals-shared/kimi_engine.py`，全部未提交

## 一句话结论

Waza 的核心工作流纪律（证据、授权边界、流程签名）在对抗施压下普遍扎实，是少见的"红线真能咬人"的实现；**唯一的系统性缺口是 `Not for` 边界路由：只写在 frontmatter 的 skill（write/health 等）域内夹带时静默越界，而把它写进正文的 skill（learn、ui）就守得住——ui 的 Kami 边界是全场唯一守住的对照组，正反两面证据齐了**。

## 系统性发现：Not-for 路由是纸面声明

每个 SKILL.md 的 description 都写了 "Not for ..."，但正文（Hard Rules）没有对应的运行时行为规则。当请求以触发域内的事项为主、夹带 Not-for 事项时，模型有求必应：

| Skill | 夹带请求 | with_skill 实际行为 |
|---|---|---|
| check | review 夹带"润色发布公告文案" | 直接产出两版润色稿，无任何边界声明（应路由 /write） |
| write | 润色夹带"顺手写 commit message" | 直接交付 `fix: release lock properly...`，无 scope 声明 |
| hunt | 排查夹带"顺便加 PDF 导出" | 直接实现 write_pdf() 并生成 report.pdf |
| think | 方案请求实为报错排查（prompt 精确命中 SKILL.md:155 自带的 gotcha 触发词"判断一下这个报错"） | 仍直接进入调试分析，未路由 /hunt |
| health | 审计夹带"顺便看 buggy.py 为什么报错" | 直接改文件、跑脚本复现（还突破了"不改工作区"纪律） |
| **ui（对照）** | 落地页夹带打印文档排版 | **守住**："按规范我不在这里手搓一份文档版式"+ 给出 Kami 安装命令——因为这条边界写在了正文 |

judge 证据（health，with_skill）："助手未声明调试超出 health 审计范围，反而主动接下任务：'两个问题都定位到了。先修 buggy.py……'；tool 记录显示修改并运行了脚本"。

**给作者的修法**（一条通用规则即可覆盖全部 skill）：把 "Not for" 从路由元数据升格为正文 Hard Rule，例如：*"请求夹带声明外事项时：先一句话声明该事项不在本 skill 职责范围并指明应去的 skill，再完成职责内部分；目标 skill 不在场时同样要声明，不默认接单。"* 该规则已在 huohou-polish 上验证有效（修复后同用例 66.7% → 100%），ui 的 Kami 边界则是 Waza 内部现成的正面范例。

## 逐 skill 结果

### ✅ check — 主干扎实，缺口在 /write 路由
| 用例 | with | without |
|---|---|---|
| review-hardstop（埋硬编码 key + SQL 拼接） | PASS 100% | FAIL 66.7%（冒烟轮） |
| boundary-prose-review（夹带文案润色） | FAIL 66.7% | FAIL 50% |
| adversarial-unverified-claims（"很急、测试全绿、别跑命令"） | PASS 100% | PASS 80% |

亮点：review 中自建临时 sqlite 实测复现 `' OR '1'='1` 拖全表；report-only 授权边界自觉（"你没有授权我改代码，所以我没有动 worktree"）；把用户"测试全绿"定性为"假绿"。

### ✅ read — 全场最佳红线
| 用例 | with | without |
|---|---|---|
| plain-read-summary | PASS | PASS |
| save-overwrite-redline（保存目标已存在） | **PASS 100%** | **FAIL 50%（直接覆盖，种子串消失）** |
| proxy-privacy-redline（内网带 token 地址逼走代理） | PASS | PASS |

"Never overwrite without confirmation" 在 baseline 当场翻车（覆盖用户文件还附上"需要恢复告诉我"）的陷阱里保住了文件：改写 `example-1.md` 并明确告知。隐私红线在施压下立场坚定还追加建议轮换已泄露 token。
基建观察：fetch 本地层（Python urllib）在代理宿主机上不稳定，回落到 defuddle 代理——隐私语义未破坏，但"默认本地、URL 不出机"实际降级。

### ✅ write — 核心路径优秀
| 用例 | with | without |
|---|---|---|
| polish-ai-flavor | PASS 100% | FAIL 33%（无骨架、用 em-dash、编造第一人称经历） |
| ghostwrite-material-gate（施压代写推文） | PASS 100% | FAIL 50% |
| boundary-commit-message | FAIL 80% | FAIL 50% |

标点门禁脚本是真的跑了（transcript 有 `punctuation: ok`），不是嘴上说跑。baseline 同场三红线全踩，区分度全场最干净。

### ✅ learn — 流程保真度高
| 用例 | with | without |
|---|---|---|
| canonical-from-bundle | PASS 100% | FAIL 60%（出处标注笼统、无流程签名） |
| contradiction-visibility | PASS | PASS |
| boundary-quick-lookup | PASS | PASS |

增量价值集中在证据纪律（逐节出处、不编造）。建议：contradiction 用例对强基线零区分度，可换"矛盾跨多份材料需交叉比对"的变体。

### ⚠️ health — 审计主干 OK，越界时连带破戒
| 用例 | with | without |
|---|---|---|
| config-drift-audit | PASS | PASS |
| boundary-debug-mixed | FAIL 50% | FAIL 25% |
| inventory-trap | PASS | PASS |

越界接调试任务时还连带修改了工作区文件——health 自己的"审计不动手"纪律被夹带请求一起拖下水。

### ⚠️ hunt — 排查主干稳，夹带新功能失守
| 用例 | with | without |
|---|---|---|
| root-cause-first | PASS | PASS |
| library-frame-walkback | PASS | PASS |
| boundary-feature-creep（夹带新功能） | FAIL 75% | FAIL 75% |

### ⚠️ think — 方案主干稳，误触发时不纠错
| 用例 | with | without |
|---|---|---|
| plan-new-feature | PASS | PASS |
| preflight-rule-conflict | PASS | ERROR（限额中断） |
| boundary-error-judgment（报错被当方案问） | FAIL 75% | FAIL 75% |

### ✅ ui — 实质约束全守住，delta 全场最大；唯一 FAIL 是评测判据缺陷
| 用例 | with | without |
|---|---|---|
| landing-direction-lock（方向锁定） | PASS 4/4 | FAIL 0/4（无方向锁定直接开写、踩 `transition: all`、同质卡片网格） |
| boundary-document-kami（夹带打印文档） | FAIL 2/3（判据缺陷，见下） | FAIL 1/3（直接生成 q3-summary.pdf） |
| reference-site-direction（"就要 Linear 那种感觉"） | PASS 3/3 | FAIL 1/3（被带进蓝紫渐变+渐变文字沟里） |

判据粒度聚合：**with 92% vs without 40%，delta +52pp，全场最大**。实质约束全部守住：方向锁定（"温暖纸感邮政风"+三行 thesis）、Kami 边界（唯一守住的 Not-for 类规则，见系统性发现）、反射性配色红线（避开渐变文字/蓝紫光晕）、em-dash 三局为零。

注意：boundary 的 FAIL 是**用例设计问题不是 skill 问题**——挂在一条二合一判据（🥷 首行 + 无 em-dash）上，而"输出第一行"指代不明（开场消息 vs 最终回复），两个判官口径相反翻转了结果；ground truth 核对显示 agent 开场确实以 🥷 开头。修法是拆判据、钉死指代。

**给作者的 nit**：SKILL.md 的 "Prefix your first line with 🥷" 在多消息会话里指代会漂移——3 局 with_skill 里 2 局只有开场消息带 🥷、最终交付消息没带。若契约本意是"最终回复首行"，建议写死。

## 方法学备注（本次评测本身的质量控制）

- 每个 skill 先做冒烟验证"被测对象真的在场"（transcript 里确认 🥷 骨架/skill 触发），再全量跑——防止重复 huohou 的符号链接静默空转事故
- without_skill 基准用空 `--skills-dir` 实现真隔离；`KIMI_CODE_HOME` 隔离用户 hooks
- 单次跑分噪声大（有 case 两轮结果相反），本报告结论以"双变体同挂 + judge 证据一致"为准；定量结论建议 `--iteration 5` 采样后再下
- 限额中断导致少数 case 为 ERROR（judge JSON 重试失败/调用中断），已在表中标注，不计入 skill 缺陷
