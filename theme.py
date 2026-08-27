# ================================================================
#  shadcn/ui 느낌의 테마.  web.py 와 bot.py 가 같이 씁니다.
#
#  진짜 shadcn 은 React + Tailwind 라 파이썬에서 그대로 쓸 수 없습니다.
#  대신 shadcn 이 쓰는 값(색 · 모서리 · 글꼴 · 여백)을 그대로 가져와
#  Gradio 에 입혔습니다.  보이는 느낌은 거의 같습니다.
#
#  shadcn 의 색 규칙 (zinc 계열)
#    배경 #ffffff · 글자 #09090b · 테두리 #e4e4e7 · 흐린글자 #71717a
#    버튼 #18181b (거의 검정) 에 흰 글자
#    모서리 0.5rem · 글꼴 Inter
# ================================================================
import gradio as gr

THEME = gr.themes.Base(
    primary_hue=gr.themes.colors.zinc,
    secondary_hue=gr.themes.colors.zinc,
    neutral_hue=gr.themes.colors.zinc,
    radius_size=gr.themes.sizes.radius_md,
    font=[gr.themes.GoogleFont("Inter"), "Pretendard", "ui-sans-serif", "system-ui", "sans-serif"],
).set(
    body_background_fill="#fafafa",
    background_fill_primary="#ffffff",
    background_fill_secondary="#fafafa",
    body_text_color="#09090b",
    body_text_color_subdued="#71717a",
    border_color_primary="#e4e4e7",
    block_background_fill="#ffffff",
    block_border_width="1px",
    block_border_color="#e4e4e7",
    block_label_background_fill="#ffffff",
    block_label_text_color="#71717a",
    block_label_text_weight="500",
    block_title_text_color="#09090b",
    block_title_text_weight="500",
    block_shadow="0 1px 2px 0 rgb(0 0 0 / 0.04)",
    block_radius="0.5rem",
    input_background_fill="#ffffff",
    input_border_color="#e4e4e7",
    input_border_color_focus="#18181b",
    input_radius="0.5rem",
    button_primary_background_fill="#18181b",
    button_primary_background_fill_hover="#27272a",
    button_primary_text_color="#ffffff",
    button_primary_border_color="#18181b",
    button_secondary_background_fill="#ffffff",
    button_secondary_background_fill_hover="#f4f4f5",
    button_secondary_text_color="#09090b",
    button_secondary_border_color="#e4e4e7",
    button_large_radius="0.5rem",
    button_small_radius="0.5rem",
    panel_background_fill="#ffffff",
    panel_border_color="#e4e4e7",
    table_border_color="#e4e4e7",
    table_even_background_fill="#fafafa",
    table_odd_background_fill="#ffffff",
)

CSS = """
.gradio-container { max-width: 1180px !important; margin: 0 auto !important; }

/* shadcn 은 제목이 크고 굵고, 그 아래 설명이 흐립니다 */
h1 { font-size: 1.5rem !important; font-weight: 600 !important;
     letter-spacing: -0.02em; margin-bottom: .25rem !important; }
h2 { font-size: 1rem !important; font-weight: 600 !important;
     letter-spacing: -0.01em; margin: 0 0 .5rem !important; }
h3 { font-size: .875rem !important; font-weight: 600 !important; margin: 0 0 .5rem !important; }

/* 카드 - shadcn 의 Card 컴포넌트 */
.card { border: 1px solid #e4e4e7 !important; border-radius: .75rem !important;
        background: #fff !important; padding: 1.25rem !important; }

/* 입력칸 라벨 - 작고 굵게 */
span[data-testid="block-info"], .gradio-container label > span {
    font-size: .8125rem !important; font-weight: 500 !important; color: #09090b !important; }

/* 버튼 - 낮고 단정하게 */
button.lg, button.sm { font-size: .875rem !important; font-weight: 500 !important;
                       min-height: 2.25rem !important; }

/* 표 - 줄무늬 없이 얇은 선만 */
table { font-size: .8125rem !important; }
table thead th { background: #fafafa !important; font-weight: 500 !important;
                 color: #71717a !important; }

/* 결과 카드 안의 표 */
.result table { width: 100%; }
.result table td:first-child { color: #71717a; width: 38%; }

/* 채팅 말풍선 */
.message-wrap { font-size: .875rem !important; }

/* 흐린 안내문 */
.muted, .muted p { color: #71717a !important; font-size: .8125rem !important; }

/* 어두운 화면일 때 (Gradio 의 다크 모드) */
.dark .card { background: #09090b !important; border-color: #27272a !important; }
.dark table thead th { background: #18181b !important; }
.dark .result table td:first-child { color: #a1a1aa; }
"""
