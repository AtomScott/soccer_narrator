# prompts.py

# Stage 1 Prompts: Independent Image Description
SINGLE_FRAME_FOCUS = "Describe exactly what you see in this single frame. Focus on player positions, actions being taken, and any noteworthy elements of this particular moment, without referencing past or future events."
SNAPSHOT_ANALYSIS = "Analyze this standalone image, detailing the football action it captures. Describe player movements, ball location, and immediate context, like a tackle, pass, or goal attempt, as if this is the only moment you're aware of. Be structured and concise, and avoid referencing past or future events. Max 50 words."
ISOLATED_EMOTIONAL_DESCRIPTION = "Convey the emotions or intensity captured in this frame. Describe player expressions, body language, and the immediate atmosphere, such as anticipation or excitement, specific to this instant."

# Stage 2 Prompts: Sequential Narrative Creation
SEQUENTIAL_NARRATION = "Using the individual image descriptions, create a flowing narrative that tells the story of the match over time. Piece together the actions from each frame to build a sense of progression and unfolding events."
DYNAMIC_MATCH_STORYTELLING = "Craft a dynamic voiceover script that weaves the standalone descriptions into a continuous and engaging story of the game, highlighting how each moment leads to the next."
COMPREHENSIVE_MATCH_OVERVIEW = "Formulate a comprehensive overview of the match using the sequence of image descriptions. Include how each scene contributes to the overall game, linking individual actions to the broader context of the match's progression."
BRAZILLIAN_NARRATIVE = "These are frames of a video. Create a short voiceover script in the style of a super excited brazilian sports narrator who is narrating his favorite match. Your output must be in english. You must only output the narration since eall the text output will be synthesized to audio. When the ball goes into the net, you must scream GOL either once or multiple times."
JAPANESE_NARRATIVE = "These are frames of a video. 超ワクワクする日本のスポーツ実況アナウンサー風に、彼のお気に入りの試合を実況する短いボイスオーバー台本を作成してください。出力は日本語でなければなりません。テキスト出力はすべて音声合成されるため、実況のみを出力してください。ボールがネットに入ったときは、「ゴール」と一回または複数回叫ぶ必要があります。"