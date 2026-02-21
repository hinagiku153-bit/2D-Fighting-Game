
;━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
;━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



;　AIレベルの調節をしたい方はまず
;「AI調節」と言う項目を「検索」機能を使って探してください。

;　勝利演出がデフォルトでＯＦＦになってますので、
;  ＯＮにしたい方は「勝利演出設定」と言う項目を「検索」機能を使って探してください。



;━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
;━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


;AIフラグ
[Command]
name    = "AI"
command = B,B,B,B,a+b+s
time    = 0
[Command]
name    = "AI1"
command = B,B,B,B,a+b+c+s
time    = 0
[Command]
name    = "AI2"
command = B,B,B,B,a+b+c
time    = 0
[Command]
name    = "AI3"
command = B,B,B,B,a+c
time    = 0
[Command]
name    = "AI4"
command = B,B,B,a+b+c
time    = 0
[Command]
name    = "AI5"
command = B,B,B,F,a+b+c
time    = 0
[Command]
name    = "AI6"
command = B,B,B,U,a+b+c
time    = 0
[Command]
name    = "AI7"
command = B,B,B,D,a+b+c
time    = 0
[Command]
name    = "AI8"
command = B,B,D,B,a+b+c
time    = 0
[Command]
name    = "AI9"
command = B,U,B,B,a+b+c
time    = 0
[Command]
name    = "AI10"
command = B,D,B,B,a+b+c
time    = 0
[Command]
name    = "AI11"
command = F,B,B,B,a+b+c
time    = 0
[Command]
name    = "AI12"
command = B,B,F,B,a+b+c
time    = 0
[Command]
name    = "AI13"
command = B,F,B,F,a+b+c
time    = 0
[Command]
name    = "AI14"
command = B,B,D,B,a+b+s
time    = 0
[Command]
name    = "AI15"
command = F,B,B,B,a+b+c
time    = 0
[Command]
name    = "AI16"
command = B,B,D,F,a+b+c+s
time    = 0
[Command]
name    = "AI17"
command = B,B,D,F,x+y+b+s
time    = 0
[Command]
name    = "AI18"
command = B,B,D,F,x+y+b+s
time    = 0
[Command]
name    = "AI19"
command = B,B,D,F,x+a+b+s
time    = 0
[Command]
name    = "AI20"
command = B,B,D,F,x+y+s
time    = 0
[Command]
name    = "AI21"
command = B,B,D,F,x+y+c+s
time    = 0
[Command]
name    = "AI22"
command = U,F,B,B,B,a+b+c+s
time    = 0
[Command]
name    = "AI23"
command = U,B,B,D,F,a+b+c+s
time    = 0
[Command]
name    = "AI24"
command = U,B,B,D,F,x+y+b+s
time    = 0
[Command]
name    = "AI25"
command = U,B,B,D,F,x+y+b
time    = 0
[Command]
name    = "AI26"
command = U,B,B,D,F,x+a+b+s
time    = 0
[Command]
name    = "AI27"
command = U,B,B,D,F,x+y+s
time    = 0
[Command]
name    = "AI28"
command = U,B,B,D,F,x+y+c+s
time    = 0


;━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━




[Command]
name = "ulu"          ;ウルスラ
command = ~D, DB, B, D, DB, B, a
time = 40


[Command]
name = "anime_p"     ;アニメパンチ
command = ~D, DF, F, D, DF, F,  z
time = 40



[Command]
name = "ikari"          ;情熱のエフェクト
command = ~D, D, D, c
time = 30



[Command]
name = "otosi"  ;竜子投げ大爆発
command = ~F,D, z
time = 15




[Command]
name = "superhadou"  ;超稲妻弾
command = ~D, DB,  z
time = 5



[Command]
name = "hadou2"        ;稲妻弾
command = ~B, F,  z
time = 10





[Command]
name = "hadou"        ;竜巻
command = ~D,DF, z
time = 10





[Command]
name = "senpuu"     ;旋風脚
command = ~D, DB, c
time = 20


[Command]
name = "kuutyuusenpuu"  ;空中旋風脚
command = ~D, DB,  c
time = 20



[Command]
name = "kuutyuuh"  ;制空竜巻蹴り
command = ~D, D,   c
time = 15




[Command]
name = "r-k"  ;竜子キック
command = ~D, D,   z
time = 15



;;;;回避
[Command]
name = "kaihi"  
command = x+y




[Command]
name = "raigeki"        ;竜子コレダー
command = ~D,DF, c
time = 15










;------------------------------------------------------------------------------
;-| 超必殺技 |-----------------------------------------------------------------


[Command]
name = "TripleKFPalm"
command = ~D, DF, F, D, DF, F, x
time = 40

[Command]  
name = "TripleKFPalm"
command = ~D, DF, F, D, DF, F, y
time = 40

[Command]
name = "SmashKFUpper"
command = ~D, DB, B, D, DB, B, x
time = 40

[Command] 
name = "SmashKFUpper"
command = ~D, DB, B, D, DB, B, y
time = 40


;------------------------------------------------------------------------------
;-| 必殺技 |-------------------------------------------------------------------

[Command]
name = "upper_x"
command = ~F, D, DF, x

[Command]
name = "upper_y"
command = ~F, D, DF, y



[Command];カンフーつきＮＥＷ
name = "QCF_x"
command = ~D, DF, F, x

[Command]
name = "QCB_a"
command = ~D, DF, F, a

[Command]
name = "QCB_b"
command = ~D, DF, F, b


[Command]
name = "FF_a"
command = F, F, a

[Command]
name = "FF_b"
command = F, F, b

;--------------------------------------------------------
;------------------------------------------------------------
;-| キー２回連続入力 |-------------------------------------------------
[Command]
name = "FF" 
command = F, F
time = 10

[Command]
name = "BB" 
command = B, B
time = 10

;------------------------------------------------------------------------------
;-| 同時押し |-----------------------------------------------------------------
[Command]
name = "recovery"  
command = x+y
time = 1

[Command]
name = "recovery" 
command = a+b
time = 1

;------------------------------------------------------------------------------
;-| 方向キー＋ボタン |---------------------------------------------------------
[Command]
name = "down_a"
command = /$D,a
time = 1

[Command]
name = "down_b"
command = /$D,b
time = 1

;------------------------------------------------------------------------------
;-| ボタン単発 |---------------------------------------------------------------
[Command]
name = "a"
command = a
time = 1

[Command]
name = "b"
command = b
time = 1

[Command]
name = "c"
command = c
time = 1

[Command]
name = "x"
command = x
time = 1

[Command]
name = "y"
command = y
time = 1

[Command]
name = "z"
command = z
time = 1

[Command]
name = "start"
command = s
time = 1

;------------------------------------------------------------------------------
;-| 方向キー押しっぱなし |-----------------------------------------------------

[Command]
name = "holdfwd" 
command = /$F
time = 1

[Command]
name = "holdback" 
command = /$B
time = 1

[Command]
name = "holdup"  
command = /$U
time = 1

[Command]
name = "holddown"
command = /$D
time = 1








;━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

;AI

;━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━




[Statedef -1]




[State -1, AI]
type = VarSet
triggerall = var(59) = 0
trigger1  = command = "AI"
trigger2  = command = "AI1"
trigger3  = command = "AI2"
trigger4  = command = "AI3"
trigger5  = command = "AI4"
trigger6  = command = "AI5"
trigger7  = command = "AI6"
trigger8  = command = "AI7"
trigger9  = command = "AI8"
trigger10  = command = "AI9"
trigger11  = command = "AI10"
trigger12  = command = "AI11"
trigger13  = command = "AI12"
trigger14  = command = "AI13"
trigger15  = command = "AI14"
trigger16  = command = "AI15"
trigger17  = command = "AI16"
trigger18  = command = "AI17"
trigger19  = command = "AI18"
trigger20  = command = "AI19"
trigger21  = command = "AI20"
trigger22  = command = "AI21"
trigger23  = command = "AI22"
trigger24  = command = "AI23"
trigger25  = command = "AI24"
trigger26  = command = "AI25"
trigger27  = command = "AI26"
trigger28  = command = "AI27"
trigger29  = command = "AI28"
v =  59
;━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

;AI調節

value = 3  ;3段階で設定可能。


; value = 1  ランダムＡＩ。 驚くほど強かったり、弱かったり・・。

; value = 2  レベル2の必殺技が低確率で発動。連続コンボなし。LV3禁止

; value = 3  すべての技を使用。コンボあり。



;━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

;ガード Lv設定

[State -1, AI]
type = VarSet
triggerall = var(58) = 0
trigger1  = var(59) > 0
v =  58

value = 5       ;0～5で調節できます

;━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


;勝利演出設定

[State -1]
type = varset
trigger1 = 1
v = 20

value = 0

; 上記の「value = 0」を以下の用に書き換えて勝利演出を設定できます。
; value = 1　勝利演出あり　　
; value = 0  勝利演出なし



;━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
;━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
;━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━




;リカバー
[State -1]
type = Changestate
triggerall   = var(59) =3
triggerall = RoundState = 2
triggerall = HitShakeOver
triggerall = life != 0
trigger1 = StateNo = 5050
trigger1 = random < 40
trigger1 = ctrl
value = 5210









;情熱のエフェクト
[State -1, ikari]
type = ChangeState
value = 6460
triggerall = var(59) =3
triggerall = roundstate = 2
triggerall = p2life > 0
triggerall = life != 0
triggerall = power >= 3000 
triggerall = statetype != A
trigger1 = ctrl 
trigger1 = random < 500






;アニメパンチ
[State -1, anime_p]
type = ChangeState
value = 6470
triggerall = p2life > 0
triggerall = life != 0
triggerall = roundstate = 2
triggerall = power >= 2000 
triggerall = power <= 2600  
triggerall = statetype != A
triggerall = p2statetype != L  
triggerall = P2movetype  != H 
triggerall = ctrl
triggerall = p2statetype != A

trigger1 = random < 250
trigger1   = var(59) =3

trigger2 = random < 10
trigger2 = life < 200
trigger2 = var(59) =2





;闘神ウルスラ
[State -1, ulu]
type = ChangeState
value = 6060
triggerall = power >= 2000
triggerall = power <= 2600 
triggerall = statetype != A
triggerall = stateno != 6470   ;アニメパンチ 
triggerall = stateno != 6471   ;アニメパンチ 
triggerall = stateno != 7200   ;竜子投げ大爆発
triggerall = stateno != 7400   ;竜子投げ大爆発
triggerall = stateno != 7600   ;竜子投げ大爆発
triggerall = stateno != 800    ;投げ
triggerall = stateno != 810    ;投げ
triggerall = ctrl 
triggerall = p2bodydist X < 250
triggerall = p2life > 0
triggerall = life != 0
triggerall = roundstate = 2

trigger1 = random < 250
trigger1   = var(59) =3

trigger2 = random < 10
trigger2   = var(59) =2
trigger2 = life < 200










;━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━




;スマッシュアッパー
[State -1]
type = ChangeState
value = 3050
triggerall = statetype != A
triggerall = power >= 1000
triggerall = power <= 1800
triggerall = ctrl 
triggerall = p2statetype != A
triggerall = P2movetype  = A
triggerall = p2bodydist X < 150
triggerall = p2bodydist X > 40
triggerall = roundstate = 2
triggerall = p2life > 0
triggerall = life != 0

trigger1 = random < 300
trigger1   = var(59) =3

trigger2 = random < 50
trigger2   = var(59) =2





;三烈突き手
[State -1]
type = ChangeState
value = 3000
triggerall = power > 1000
triggerall = power <= 1800
triggerall = statetype != A
triggerall = ctrl
triggerall = p2bodydist X < 150
triggerall = p2bodydist X > 20
triggerall = p2statetype != L
triggerall = p2statetype != A
triggerall = p2movetype = A
triggerall = roundstate = 2
triggerall = p2life > 0
triggerall = life != 0

trigger1 = random < 300
trigger1   = var(59) =3

trigger2 = random < 50
trigger2   = var(59) =2






;制空竜巻蹴り
[State -1, kuutyuuh]
type = ChangeState
value = 6760
triggerall = power >= 1000 
triggerall = power <= 1800
triggerall = statetype = A
triggerall = ctrl 
triggerall = p2bodydist X < 70
triggerall = p2bodydist X > -20
triggerall = p2bodydist y >= -60
triggerall = p2bodydist y <= 0
triggerall = roundstate = 2
triggerall = p2life > 0
triggerall = life != 0

trigger1 = random < 400
trigger1   = var(59) =3

trigger2 = random < 50
trigger2   = var(59) =2






;竜子キック
[State -1]
type = ChangeState
value = 8040
triggerall = statetype != A
triggerall = movetype != H
triggerall = power >= 1000
triggerall = power <= 1800
triggerall = ctrl
triggerall = roundstate = 2
triggerall = p2life > 0
triggerall = life != 0

trigger1 = random < 40
trigger1 = p2bodydist X < 80
trigger1 = p2bodydist X > 5
trigger1 = P2movetype  = A
trigger1   = var(59) =2

trigger2 = random < 200
trigger2 = p2bodydist X < 60
trigger2 = p2bodydist X > -10
trigger2 = P2movetype  != H
trigger2 = p2statetype = A
trigger2 = var(59) =3

trigger3 = random < 200
trigger3 = p2bodydist X < 0
trigger3 = p2bodydist X > -50
trigger3 = P2movetype  != H
trigger3 = p2statetype != A
trigger3 = var(59) =3







;超稲妻弾
[State -1]
type = ChangeState
value = 7999
triggerall = statetype != A
triggerall = power >= 1000
triggerall = power <= 1800
triggerall = roundstate = 2
triggerall = p2life > 0
triggerall = life != 0
triggerall = ctrl

trigger1 = P2movetype  = A
trigger1 = random < 30
trigger1 = p2bodydist X > 120
trigger1   = var(59) =2

trigger2 = P2movetype  = A
trigger2 = random < 200
trigger2 = p2bodydist X > 100
trigger2   = var(59) =3

trigger3 = random < 200
trigger3 = enemy, Numproj > 0
trigger3   = var(59) =3

trigger4 = P2movetype  = A
trigger4 = P2statetype  != L
trigger4 = P2stateno  != 5200
trigger4 = random < 200
trigger4 = enemy, numhelper > 0
trigger4 = var(59) =3





;━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



;ダッシュ
[State -1]
type = ChangeState
value = 101000
triggerall = statetype != A
triggerall = roundstate = 2
triggerall = p2life > 0
triggerall = ctrl
triggerall = var(59) =3
triggerall = life != 0

trigger1 = p2bodydist X > 120
trigger1 = p2statetype != A
trigger1 = random < 60
trigger1 = p2movetype = I






;;竜巻攻撃
[State -1]
type = ChangeState
value = 6040
triggerall = statetype != A
triggerall = roundstate = 2
triggerall = p2life > 0
triggerall = life != 0
triggerall = ctrl 
triggerall = p2statetype != L  
triggerall = numProjID(0001) = 0
triggerall = numProjID(0000) = 0

trigger1 = p2bodydist X > 120
trigger1 = p2statetype != A
trigger1 = random < 200
trigger1 = var(59) =3

trigger2 = p2bodydist X > 120
trigger2 = p2statetype != A
trigger2 = random < 20
trigger2 = var(59) =2






;;稲妻弾
[State -1]
type = ChangeState
value = 6041
triggerall = statetype != A
triggerall = roundstate = 2
triggerall = p2life > 0
triggerall = life != 0
triggerall = ctrl
triggerall = statetype != A
triggerall = p2bodydist X > 100
triggerall = p2statetype != A 
triggerall = p2statetype != L  
triggerall = numProjID(0000) = 0
triggerall = numProjID(0001) = 0

trigger1 = random < 200
trigger1   = var(59) =3

trigger2 = random < 50
trigger2   = var(59) =2





;アッパー
[State -1]
type = ChangeState
value = 1100
triggerall = life != 0
triggerall = p2life > 0
triggerall = roundstate = 2
triggerall = statetype !=A

trigger1 = P2movetype  = A
trigger1 = p2statetype !=A
trigger1 = p2statetype !=L
trigger1 = random < 20
trigger1 = p2bodydist X < 100
trigger1 = p2bodydist X > 0
trigger1 = ctrl
trigger1   = var(59) =2

trigger2 = P2movetype  = A
trigger2 = p2statetype !=A
trigger2 = p2statetype !=L
trigger2 = random < 50
trigger2 = p2bodydist X < 100
trigger2 = p2bodydist X > 0
trigger2 = ctrl
trigger2   = var(59) =3

trigger3 = p2bodydist X > 100
trigger3 = p2bodydist X < 150
trigger3 = random < 100
trigger3 = ctrl
trigger3 = P2movetype  = A
trigger3   = var(59) =3

trigger4 = (stateno = 239) && time > 32   ;特殊強キック1
trigger4 = movehit
trigger4 = var(59) =3
trigger4 = random < 60





;ヒザ蹴り
[State -1]
type = ChangeState
value = 1060
triggerall = var(59) =3
triggerall = roundstate = 2
triggerall = p2life > 0
triggerall = life != 0

trigger1 = stateno = 3000
trigger1  = animtime = 0
trigger1 = movehit

trigger2 = Stateno = 230
trigger2 = movehit
trigger2 = random < 200

trigger3 = stateno = 5121
trigger3 = animtime = 0
trigger3 = movehit
trigger3 = p2statetype = A
trigger3 = var(59) =3








追撃蹴り
[State -1]
type = ChangeState
value = 1055
triggerall = var(59) =3
triggerall = roundstate = 2
triggerall = p2life > 0
triggerall = life != 0

trigger1 = p2life > 0
trigger1 = stateno = 1061






追撃蹴り2
[State -1]
type = ChangeState
value = 10555
triggerall = var(59) =3
triggerall = roundstate = 2
triggerall = p2life > 0
triggerall = life != 0

trigger1 = stateno = 1055
trigger1 = AnimElem = 8
trigger1 = random < 100





;旋風脚
[State -1]
type = ChangeState
value = 6400
triggerall = life != 0
triggerall = statetype != A
triggerall = roundstate = 2

trigger1 = p2bodydist X > 0
trigger1 = p2bodydist X < 100
trigger1 = p2statetype = A
trigger1 = P2movetype  = A
trigger1 = ctrl
trigger1 = random < 100
trigger1 = var(59) =3




;旋風脚
[State -1]
type = ChangeState
value = 6400
triggerall = life != 0
triggerall = statetype != A
triggerall = roundstate = 2

trigger1 = P2movetype  = A
trigger1 = p2statetype = A
trigger1 = random < 40
trigger1 = p2bodydist X < 100
trigger1 = var(59) =2
trigger1 = ctrl

trigger2 = stateno = 610
trigger2 = movehit
trigger2 = animtime = 0
trigger2 = p2movetype = H
trigger2 = var(59) =3

trigger3 = stateno = 410
trigger3 = movehit
trigger3 = animtime = 0
trigger3 = var(59) =3

trigger4 = stateno = 101000
trigger4 = var(59) =3
trigger4 = p2statetype = A
trigger4 = p2bodydist X < 70
trigger4 = p2bodydist X > -20

trigger5 = stateno = 208;特殊強パンチ
trigger5 = movehit
trigger5 = p2bodydist y <= -71

trigger6 = stateno = 238;特殊強キック2
trigger6 = movehit
trigger6 = random < 60
trigger6 = p2bodydist y <= -71









;空中旋風脚
[State -1]
type = ChangeState
value = 6710
triggerall = life != 0
triggerall = var(59)  = 3
triggerall = statetype != S
triggerall = stateno != 6760   ;空中超必
triggerall = stateno != 8040   ;竜子キック
triggerall = stateno != 8041   ;竜子キック
triggerall = stateno != 8042   ;竜子キック
triggerall = stateno != 6710   ;空中旋風脚 
triggerall = roundstate = 2
triggerall = p2life > 0

trigger1 = stateno = 1055
trigger1 = movehit 
trigger1 = random < 100

trigger2 = stateno = 1060
trigger2 = movehit 
trigger2 = random < 40

trigger3 = statetype = A
trigger3 = p2bodydist X < 150
trigger3 = p2bodydist X > -150
trigger3 = p2statetype = A
trigger3 = p2movetype = A
trigger3 = ctrl





;突き手
[State -1]
type = ChangeState
value = 1020
triggerall = var(59)  = 2
triggerall = statetype != A
triggerall = roundstate = 2
triggerall = p2life > 0
triggerall = p2statetype != L
triggerall = p2stateno != 5120
triggerall = life != 0

trigger1 = random < 30
trigger1 = p2statetype != A
trigger1 = p2bodydist X > 200
trigger1 = ctrl




;突き手
[State -1]
type = ChangeState
value = 1020
triggerall = var(59)  = 3
triggerall = statetype != A
triggerall = roundstate = 2
triggerall = p2life > 0
triggerall = p2statetype != L
triggerall = p2stateno != 5120
triggerall = life != 0

trigger1 = stateno = 6040
trigger1  = animtime = 0
trigger1 = random < 70

trigger2 = statetype != A
trigger2 = stateno = 440
trigger2 = movehit

trigger3 = random < 50
trigger3 = p2statetype != A
trigger3 = p2bodydist X > 200
trigger3 = ctrl

trigger4 = stateno = 208;特殊強パンチ
trigger4 = movehit
trigger4 = p2bodydist y >= -70

trigger5 = stateno = 238;特殊強キック2
trigger5 = movehit
trigger5 = random < 60
trigger5 = p2bodydist y >= -70







;竜子投げ大爆発
[State -1]
type = ChangeState
value = 7200
triggerall   = var(59) = 3
triggerall = roundstate = 2
triggerall = life != 0
triggerall = statetype != A
triggerall = p2bodydist X <   60
triggerall = p2bodydist X >   -7
triggerall = p2statetype != A
triggerall = p2statetype != L
triggerall = p2movetype != H
triggerall = p2life > 0

trigger1 = random < 100
trigger1 = ctrl








;雷撃
;[State -1]
;type = ChangeState
;value = 7800
;triggerall = var(59) = 3
;triggerall = statetype != A
;triggerall = p2bodydist X < 100
;triggerall = roundstate = 2
;triggerall = p2life > 0
;triggerall = life != 0

;trigger1 = ctrl
;trigger1   = p2statetype != A
;trigger1   = random < 10
;trigger1 = p2bodydist X > -20

;trigger2 = stateno = 410
;trigger2 = movehit
;trigger2  = animtime = 0
;trigger2 = random < 100







;竜子コレダー
[State -1]
type = ChangeState
value = 8500
triggerall = p2statetype != L
triggerall = statetype != A
triggerall = statetype != L
triggerall = movetype != H
triggerall = roundstate = 2
triggerall = ctrl
triggerall = life != 0

trigger1 = var(59) = 2
trigger1 = p2statetype = A
trigger1 = p2bodydist X < 40
trigger1 = p2bodydist X > -20
trigger1 = random < 30

trigger2 = var(59) = 3
trigger2 = p2statetype = A
trigger2 = p2bodydist X < 40
trigger2 = p2bodydist X > -20
trigger2 = random < 100







;空中反動蹴り3
[State -1]
type = ChangeState
value = 85301
triggerall = statetype = A
triggerall = roundstate = 2
triggerall = var(59) = 3
triggerall = p2life > 0
triggerall = life != 0

trigger1 = p2bodydist X > 130
trigger1 = p2statetype = A
trigger1 = P2movetype  = A
trigger1 = random < 200
trigger1 = ctrl






;空中反動蹴り2
[State -1]
type = ChangeState
value = 85300
triggerall = statetype = A
triggerall = roundstate = 2
triggerall = life > 0
triggerall = var(59) = 3

trigger1 = p2bodydist X > 50
trigger1 = p2bodydist X < 150
trigger1 = p2statetype = A
trigger1 = P2movetype  = A
trigger1 = random < 200
trigger1 = ctrl

trigger2 = stateno = 5210
trigger2 = p2bodydist X > 50
trigger2 = p2bodydist X < 120
trigger2 = P2movetype  = A
trigger2 = random < 100




;空中反動蹴り1
[State -1]
type = ChangeState
value = 8530
triggerall = statetype = A
triggerall = roundstate = 2
triggerall = life > 0
triggerall = var(59) = 3

trigger1 = p2bodydist X > -10
trigger1 = p2bodydist X < 40
trigger1 = P2movetype  = A
trigger1 = random < 200
trigger1 = ctrl













;━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━







;投げ
[State -1, Throw]
type = ChangeState
value = 800
triggerall = roundstate = 2
triggerall = statetype != A
triggerall = stateno != 100
triggerall = p2bodydist X < 10
triggerall = p2bodydist X > -3
triggerall = p2statetype != A && p2movetype != H
triggerall = p2statetype != L
triggerall = ctrl
triggerall = p2life > 0
triggerall = life != 0

trigger1 = random < 200
trigger1   = var(59) =3

trigger2 = random < 50
trigger2   = var(59) =2








;ジャンプ強パンチ
[State -1,1]
type = ChangeState
value = 610
triggerall = var(59) > 0
triggerall = statetype = A
triggerall   = p2statetype != L 
triggerall   = P2movetype  != A  
triggerall = roundstate = 2
triggerall = p2life > 0
triggerall = life != 0

trigger1 = p2statetype != A
trigger1 = ctrl 
trigger1 = pos Y > -50
trigger1 = vel y>-1
trigger1 = p2bodydist X < 70
trigger1 = p2bodydist X > -20

trigger2 = stateno = 7900
trigger2 = p2bodydist X < 100
trigger2 = p2bodydist X > -20

trigger3 = p2statetype = A
trigger3 = ctrl 
trigger3 = p2bodydist X < 150
trigger3 = p2bodydist X > -20
trigger3 = random < 70






;ジャンプ強キック
[State -1,1]
type = ChangeState
value = 640
triggerall = var(59) > 0
triggerall = statetype = A
triggerall   = p2statetype != L 
triggerall   = P2movetype  != A 
triggerall = roundstate = 2
triggerall = p2life > 0
triggerall = life != 0

trigger1 = p2statetype = A
trigger1 = ctrl 
trigger1 = p2bodydist X < 150
trigger1 = p2bodydist X > -20







;しゃがみ弱パンチ1
[State -1]
type = ChangeState
value = 400
triggerall   = var(59)  = 2 && roundstate = 2
triggerall = p2statetype != L
triggerall = p2statetype != A
triggerall   = p2stateno != 5120 
triggerall = p2bodydist X < 45
triggerall = p2bodydist X > 0
triggerall = life != 0

trigger1 = p2life > 0
trigger1 = statetype != A
trigger1 = ctrl
trigger1   = random < 70




;しゃがみ弱パンチ2
[State -1]
type = ChangeState
value = 400
triggerall = var(59)  = 3 && roundstate = 2
triggerall = p2statetype != L
triggerall = p2statetype != A
triggerall = p2stateno != 5120 
triggerall = p2bodydist X < 45
triggerall = p2bodydist X > 0
triggerall = life != 0

trigger1 = p2life > 0
trigger1 = statetype != A
trigger1 = ctrl
trigger1   = random < 300





;しゃがみ弱キック1
[State -1]
type = ChangeState
value = 430
triggerall   = var(59)  = 2 && roundstate = 2
triggerall = p2statetype != A
triggerall = p2bodydist X < 45
triggerall = p2bodydist X > 0
triggerall = p2life > 0
triggerall = ctrl
triggerall = life != 0

trigger1 = statetype != A
trigger1 = ctrl
trigger1   = random < 70







;しゃがみ弱キック2
[State -1]
type = ChangeState
value = 430
triggerall   = var(59)  = 3 && roundstate = 2
triggerall = p2statetype != A
triggerall = p2bodydist X < 45
triggerall = p2bodydist X > 0
triggerall = p2life > 0
triggerall = ctrl
triggerall = life != 0

trigger1 = statetype != A
trigger1   = random < 300






;特殊強パンチ
[State -1, Stand Strong Punch]
type = ChangeState
value = 209
triggerall = var(59) > 0
triggerall = statetype != A
triggerall = roundstate = 2
triggerall = p2life > 0
triggerall = life != 0

trigger1 = ctrl
trigger1   = p2statetype != A       ; Not Lie down
trigger1   = p2statetype != L       ; Not Lie down
trigger1   = random < 30
trigger1 = p2bodydist X > 50
trigger1 = p2bodydist X < 120

trigger2 = (stateno = 210) && time > 15
trigger2 = movehit

trigger3 = (stateno = 229) && time > 42
trigger3 = movehit
trigger3 = p2bodydist X < 70
trigger3 = p2bodydist y >= -70






;立ち強パンチ
[State -1, Stand Strong Punch]
type = ChangeState
value = 210
triggerall = var(59) > 0
triggerall = statetype != A
triggerall = p2bodydist X > 30
triggerall = p2bodydist X < 100
triggerall = roundstate = 2
triggerall = p2life > 0
triggerall = life != 0

trigger1 = ctrl
trigger1   = p2statetype != A       ; Not Lie down
trigger1   = p2statetype != L       ; Not Lie down
trigger1   = random < 70

trigger2 = (stateno = 240) && time > 12
trigger2 = movehit
trigger2   = random < 70







;特殊強キック

[State -1, Standing Strong Kick]
type = ChangeState
value = 239
triggerall = var(59)  > 0
triggerall = p2statetype != L
triggerall = statetype != A
triggerall = roundstate = 2
triggerall = p2life > 0
triggerall = life != 0

trigger1 = random < 50
trigger1 = p2bodydist X > 40
trigger1 = p2bodydist X < 70
trigger1 = ctrl

trigger2 = (stateno = 240) && time > 13
trigger2 = movehit

trigger3 = stateno = 198
trigger3 = movehit
trigger3 = p2bodydist X < 70







;立ち強キック
[State -1, Standing Strong Kick]
type = ChangeState
value = 240
triggerall = var(59) > 0
triggerall = statetype != A
triggerall = p2bodydist X > 30
triggerall = p2bodydist X < 100
triggerall = roundstate = 2
triggerall = p2life > 0
triggerall = life != 0

trigger1 = ctrl
trigger1   = p2statetype != A       ; Not Lie down
trigger1   = p2statetype != L       ; Not Lie down
trigger1   = random < 70

trigger2 = (stateno = 210) && time > 15
trigger2 = movehit
trigger2 = random < 70
trigger2 = p2statetype != A







;しゃがみ強パンチ
[State -1]
type = ChangeState
value = 410
triggerall   = var(59) = 3
triggerall = p2statetype != L
triggerall = statetype != A
triggerall = statetype != L
triggerall = movetype != H
triggerall = roundstate = 2
triggerall = ctrl
triggerall = life != 0

trigger1 = p2statetype = A
trigger1 = p2bodydist X < 70
trigger1 = p2bodydist X > -20
trigger1 = p2bodydist y >= -130
trigger1   = random < 70









;しゃがみ強キック
[State -1]
type = ChangeState
value = 440
triggerall   = var(59)  > 1
triggerall = p2statetype != A
triggerall   = p2stateno != 5120 
triggerall = statetype != A
triggerall = roundstate = 2
triggerall = p2life > 0
triggerall = life != 0

trigger1 = p2bodydist X < 100
trigger1 = p2bodydist X > 50
trigger1 = p2life > 1
trigger1 = statetype != A
trigger1 = ctrl
trigger1   = random < 80

trigger2 = stateno = 430
trigger2 = p2bodydist X > 34
trigger2 = movehit

trigger3 = stateno = 229
trigger3 = p2movetype = H
trigger3 = animtime = 0






;特殊弱パンチ
[State -1, Stand Strong Punch]
type = ChangeState
value = 199
triggerall   = var(59)  > 0 && roundstate = 2
triggerall = p2statetype != A
triggerall = p2life > 0
triggerall = statetype != A
triggerall   = p2statetype != L 
triggerall = p2life > 0
triggerall = life != 0

trigger1 = p2bodydist X < 70
trigger1 = p2bodydist X > 21
trigger1 = ctrl
trigger1 = random < 70

trigger2 = stateno = 200
trigger2 = p2bodydist X > 20
trigger2 = movehit







;立ち弱パンチ
[State -1]
type = ChangeState
value = 200
triggerall   = var(59)  > 0 && roundstate = 2
triggerall = p2life > 0
triggerall = p2statetype != A
triggerall = statetype != A
triggerall = p2statetype != L 
triggerall = p2life > 0
triggerall = life != 0

trigger1 = p2bodydist X < 30
trigger1 = p2bodydist X > 0
trigger1 = ctrl
trigger1   = random < 70







;特殊弱キック

[State -1]
type = ChangeState
value = 229
triggerall   = var(59)  > 0 && roundstate = 2
triggerall = p2statetype != A
triggerall = statetype != A
triggerall   = p2statetype != L 
triggerall   = p2stateno != 5120 
triggerall = p2life > 0
triggerall = life != 0

trigger1 = p2bodydist X < 70
trigger1 = p2bodydist X > 20
trigger1 = ctrl
trigger1 = random < 70

trigger2 = stateno = 230
trigger2 = movehit
trigger2 = ctrl
trigger2 = p2bodydist X > 20
trigger2 = random < 40

trigger3 = stateno = 200
trigger3 = animtime = 0
trigger3 = random < 50
trigger3 = p2bodydist X < 100
trigger3 = p2bodydist X > 0








;立ち弱キック
[State -1]
type = ChangeState
value = 230
triggerall   = var(59)  > 0 && roundstate = 2
triggerall = p2statetype != A
triggerall = p2life > 0
triggerall = statetype != A
triggerall   = p2statetype != L 
triggerall = life != 0

trigger1 = p2bodydist X < 30
trigger1 = p2bodydist X > 0
trigger1 = ctrl
trigger1 = random < 70





;━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
;━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━














;バックステップ2
[State -1, Back Step]
type = ChangeState
value = 105
triggerall   = var(59)  = 3 && roundstate = 2
triggerall   = statetype != A
triggerall   = movetype != H
triggerall = p2bodydist X > -10
triggerall = p2life > 0
triggerall = life != 0

trigger1 = ctrl
trigger1   = stateno = 106
trigger1   = p2movetype = A
trigger1 = p2bodydist X < 60

trigger2 = ctrl
trigger2 = p2bodydist X < 60
trigger2 = p2bodydist X > 0
trigger2   = random < 60
trigger2   = P2movetype  = A

trigger3 = ctrl
trigger3 = p2statetype = L
trigger3 = p2bodydist X < 100

trigger4 = ctrl
trigger4 = p2stateno = 5120
trigger4 = p2bodydist X < 100







;バックステップ3
[State -1, Back Step]
type = ChangeState
value = 105
triggerall   = var(59)  =3 && roundstate = 2
triggerall   = statetype != A
triggerall   = movetype != H
triggerall = life != 0

trigger1 = stateno = 800
trigger1  = p2bodydist X < 0

trigger2 = stateno = 8500
trigger2 = time = 50
trigger2 = p2bodydist X < 50
trigger2 = p2bodydist X > -30






;回避1
[State -1]
type = ChangeState
value = 60300
triggerall   = var(59)  =3 && roundstate = 2
triggerall = p2life > 0
triggerall = statetype != A
triggerall = p2statetype != L
triggerall = movetype != H
triggerall = ctrl
triggerall = life != 0

trigger1   = P2movetype  = A
trigger1 = p2bodydist X > 100
trigger1   = random < 50
trigger1 = enemy, numhelper > 0

trigger2 = p2bodydist X < 100
trigger2   = random < 40
trigger2   = P2movetype  = A

trigger3   = P2movetype  = A
trigger3 = p2bodydist X > 100
trigger3   = random < 50
trigger3 = enemy, Numproj > 0

trigger4 = p2bodydist X > 100
trigger4   = random < 30
trigger4   = P2movetype  = A

trigger5 = stateno =5121
trigger5 = AnimTime = 0
trigger5 = p2bodydist X < 40
trigger5 = p2bodydist X > -40

trigger6 = p2bodydist X < 50
trigger6 = p2bodydist X > 0
trigger6   = random < 20
trigger6   = P2movetype  = A

trigger7 = p2bodydist X < 250
trigger7 = p2bodydist X > 100
trigger7 = random < 100
trigger7 = P2movetype  = A

trigger8   = P2movetype  = A
trigger8 = p2bodydist X < 40
trigger8   = random < 30
trigger8 = enemy, numhelper > 0

trigger9 = p2bodydist X > 100
trigger9   = random < 70






;回避2
[State -1]
type = ChangeState
value = 60300
triggerall = var(59)  =3 && roundstate = 2
triggerall = p2life > 0
triggerall = life != 0
triggerall = statetype != A
triggerall = p2statetype != L
triggerall = movetype != H
;triggerall = ctrl

;trigger1 = random < 70
trigger1 = stateno = 7200
trigger1 = time  =  1
trigger1 = P2movetype  = A

trigger2 = stateno = 101
trigger2 = P2movetype  = A

trigger3 = stateno = 105
trigger3 = animtime = 0
trigger3 = p2bodydist X < 100
trigger3 = p2bodydist X > -10
trigger3 = p2statetype = L

trigger4 = stateno = 105
trigger4 = animtime = 0
trigger4 = p2bodydist X < 100
trigger4 = p2bodydist X > -10
trigger4 = p2stateno = 5120

trigger5 = stateno = 101000
trigger5 = P2movetype  = A

trigger6 = stateno = 101000
trigger6 = p2bodydist X < 70




;回避3
[State -1]
type = ChangeState
value = 60300
triggerall = var(59)  =3 && roundstate = 2
triggerall = p2life > 0
triggerall = life != 0
triggerall = statetype != A
triggerall = movetype != H

trigger1 = stateno = 106
trigger1 = p2statetype = L
trigger1 = p2bodydist X < 50
trigger1 = animtime = 0







;━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━




[State -1,しゃがみガード]
Type = ChangeState
Value = 131
Triggerall = var(59) > 0
TriggerAll = StateType != A
Triggerall = inguarddist
Triggerall = Ctrl 
Triggerall = p2Statetype != A
Trigger1 = Random = [0,300]
Trigger1 = var(58) = 1
Trigger2 = Random = [0,700]
Trigger2 = var(58) = 2
Trigger3 = Random = [0,350]
Trigger3 = var(58) = 3
Trigger4 = Random = [0,700]
Trigger4 = var(58) = 4
Trigger5 = Random = [0,970]
Trigger5 = var(58) > 4


[State -1,立ちガード]
Type = ChangeState
Value = 130
Triggerall = var(59) > 0
TriggerAll = StateType != A
Triggerall = inguarddist
Triggerall = Ctrl 
Triggerall = p2Statetype = A
Trigger1 = Random = [0,300]
Trigger1 = var(58) = 1
Trigger2 = Random = [0,700]
Trigger2 = var(58) = 2
Trigger3 = Random = [0,350]
Trigger3 = var(58) = 3
Trigger4 = Random = [0,700]
Trigger4 = var(58) = 4
Trigger5 = Random = [0,970]
Trigger5 = var(58) > 4


[State -1,空中ガード]
Type = ChangeState
value = 132
Triggerall = var(59) > 0
TriggerAll = StateType = A
Triggerall = inguarddist
Triggerall = Ctrl
Trigger1 = Random = [0,300]
Trigger1 = var(58) = 1
Trigger2 = Random = [0,700]
Trigger2 = var(58) = 2
Trigger3 = Random = [0,350]
Trigger3 = var(58) = 3
Trigger4 = Random = [0,700]
Trigger4 = var(58) = 4
Trigger5 = Random = [0,970]
Trigger5 = var(58) > 4


;━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━




































;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

:::::::プレイヤー用







;闘神ウルスラ
[State -1, ulu]
type = ChangeState
value = 6060
triggerall   = var(59)  = [0,1]
triggerall = command = "ulu"
triggerall = power >= 2000
triggerall = statetype != A
triggerall = stateno != 6470
triggerall = stateno != 6471
triggerall = stateno != 6600
trigger1 = ctrl 
trigger2 = hitdefattr = SC, NA, SA, HA  
trigger3 = MoveContact = 1



;アニメパンチ
[State -1, anime_p]
type = ChangeState
value = 6470
triggerall   = var(59)  = [0,1]
triggerall = command = "anime_p"
triggerall = power >= 2500 
triggerall = statetype != A
trigger1 = ctrl 
trigger2 = hitdefattr = SC, NA, SA, HA  
trigger3 = MoveContact = 1



;情熱のエフェクト
[State -1, ikari]
type = ChangeState
value = 6460
triggerall   = var(59)  = [0,1]
triggerall = command = "ikari"
triggerall = power >= 3000 
triggerall = statetype != A
trigger1 = ctrl 
trigger2 = hitdefattr = SC, NA, SA, HA  
trigger3 = MoveContact = 1








;空中反動蹴り2
[State -1]
type = ChangeState
value = 85300
triggerall   = var(59)  = [0,1]
triggerall = command = "b"
triggerall = command = "holdfwd"
triggerall = command = "holddown"

trigger1 = statetype = A
trigger1 = ctrl





;空中反動蹴り3
[State -1]
type = ChangeState
value = 85301
triggerall   = var(59)  = [0,1]
triggerall = command = "b"
triggerall = command = "holdfwd"

trigger1 = statetype = A
trigger1 = ctrl




;空中反動蹴り1
[State -1]
type = ChangeState
value = 8530
triggerall   = var(59)  = [0,1]
triggerall = command = "b"
triggerall = command = "holddown"
trigger1 = statetype = A
trigger1 = ctrl









;竜巻攻撃
[State -1]
type = ChangeState
value = 6040
triggerall   = var(59)  = [0,1]
triggerall = command = "hadou"
triggerall = statetype != A 
triggerall = numProjID(0001) = 0
triggerall = numProjID(0000) = 0
;;;;;triggerall = NumHelper(0000) = 0
trigger1 = ctrl
trigger2 = MoveContact = 1



;竜巻攻撃Ⅱ
[State -1]
type = ChangeState
value = 6041
triggerall   = var(59)  = [0,1]
triggerall = command = "hadou2"
triggerall = statetype != A 
triggerall = numProjID(0000) = 0
triggerall = numProjID(0001) = 0
;;;;;triggerall = NumHelper(0000) = 0
trigger1 = ctrl
trigger2 = MoveContact = 1





[State -1]
type = ChangeState
value = 6400
triggerall   = var(59)  = [0,1]
triggerall = command = "senpuu"
triggerall = statetype != A 
triggerall = stateno != 3050
triggerall = stateno != 6600
triggerall = stateno != 6002
triggerall = stateno != 6060
triggerall = stateno != 6702
triggerall = stateno != 3000
triggerall = stateno != 6040
triggerall = stateno != 6400
trigger1 = ctrl 
trigger2 = MoveContact = 1

trigger3 = stateno = 3000
trigger3  = animtime = 0






[State -1]
type = ChangeState
value = 6710
triggerall   = var(59)  = [0,1]
triggerall = command = "kuutyuusenpuu"
triggerall = statetype != S 
triggerall = stateno != 3050
triggerall = stateno != 6600
triggerall = stateno != 6002
triggerall = stateno != 6060
triggerall = stateno != 6702
triggerall = stateno != 3000
triggerall = stateno != 6040
triggerall = stateno != 6400
triggerall = stateno != 6710
trigger1 = ctrl 
trigger2 = MoveContact = 1






;スマッシュカンフーアッパー（ゲージレベル１）
[State -1, Smash Kung Fu Upper]
type = ChangeState
value = 3050
triggerall = command = "SmashKFUpper"
triggerall   = var(59)  = [0,1]
triggerall = statetype != A 
triggerall = power >= 1000
triggerall = stateno != 3050
triggerall = stateno != 6600
triggerall = stateno != 6002
triggerall = stateno != 6060
triggerall = stateno != 6702
triggerall = stateno != 6470
triggerall = stateno != 6460

trigger1 = ctrl 
trigger2 = hitdefattr = SC, NA, SA, HA 

;------------------------------------------------------------------------------

;三烈突き手（ゲージレベル１）
[State -1, Triple Kung Fu Palm]
type = ChangeState
value = 3000
triggerall   = var(59)  = [0,1]
triggerall = command = "TripleKFPalm"
triggerall = statetype != A 
triggerall = power >= 1000
triggerall = stateno != [3000,3050]
triggerall = stateno != 6002
triggerall = stateno != 6060
triggerall = stateno != 6600
triggerall = stateno != 6702
triggerall = stateno != 6470
triggerall = stateno != 6460

trigger1 = statetype = S
trigger2 = ctrl 
trigger3 = hitdefattr = SC, NA, SA, HA 

;===========================================================================
;------------------------------------------------------------------------------

;アッパー（弱）
[State -1, Light Kung Fu Upper]
type = ChangeState
value = 1100
triggerall   = var(59)  = [0,1]
triggerall = command = "upper_x"
trigger1 = statetype != A
trigger1 = ctrl
trigger2 = (stateno = [200,299]) || (stateno = [400,499])
trigger2 = stateno != 440
trigger2 = movecontact

;アッパー（強）
[State -1, Strong Kung Fu Upper]
type = ChangeState
value = 1110
triggerall   = var(59)  = [0,1]
triggerall = command = "upper_y"
trigger1 = statetype != A
trigger1 = ctrl
trigger2 = (stateno = [200,299]) || (stateno = [400,499])
trigger2 = stateno != 440
trigger2 = movecontact

;------------------------------------------------------------------------------

;カンフー蹴り（弱）
[State -1, Light Kung Fu Knee]
type = ChangeState
value = 1050
triggerall   = var(59)  = [0,1]
triggerall = command = "FF_a"
trigger1 = statetype != A
trigger1 = ctrl
trigger2 = (stateno = [200,299]) || (stateno = [400,499])
trigger2 = stateno != 440
trigger2 = movecontact

;カンフー蹴り（強）
[State -1, Strong Kung Fu Knee]
type = ChangeState
value = 1060
triggerall   = var(59)  = [0,1]
triggerall = command = "FF_b"
trigger1 = statetype != A
trigger1 = ctrl
trigger2 = (stateno = [200,299]) || (stateno = [400,499])
trigger2 = stateno != 440
trigger2 = movecontact

;------------------------------------------------------------------------------
;速いカンフー突き手 NEW
[State -1, Fast Kung Fu Palm]
type = ChangeState
value = 1020
triggerall   = var(59)  = [0,1]
triggerall = command = "QCF_x"
trigger1 = statetype != A
trigger1 = ctrl
trigger2 = (stateno = [200,299]) || (stateno = [400,499])
;trigger2 = stateno != 440
trigger2 = movecontact


;ダッシュ
[State -1, Dash]
type = ChangeState
value = 100
triggerall   = var(59)  = [0,1]
trigger1 = command = "FF"
trigger1 = statetype = S
trigger1 = ctrl

;バックステップ
[State -1, Back Step]
type = ChangeState
value = 105
triggerall   = var(59)  = [0,1]
trigger1 = command = "BB"
trigger1 = statetype = S
trigger1 = ctrl





:回避
[State -1]
type = ChangeState
value = 60300
triggerall   = var(59)  = [0,1]
triggerall = command = "kaihi"
triggerall = statetype != A
trigger1 = ctrl 





;------------------------------------------------------------------------------
;投げ
[State -1, Kung Fu Throw]
type = ChangeState
value = 800
triggerall   = var(59)  = [0,1]
triggerall = command = "y"
triggerall = statetype = S
triggerall = ctrl
triggerall = stateno != 100
trigger1 = command = "holdfwd"
trigger1 = p2bodydist X < 3
trigger1 = (p2statetype = S) || (p2statetype = C)
trigger1 = p2movetype != H
trigger2 = command = "holdback"
trigger2 = p2bodydist X < 5
trigger2 = (p2statetype = S) || (p2statetype = C)
trigger2 = p2movetype != H

;==============================================================================
;------------------------------------------------------------------------------



;特殊弱パンチ
[State -1]
type = ChangeState
value = 199
triggerall   = var(59)  = [0,1]
triggerall = command = "x"
triggerall = command = "holdfwd"
trigger1 = statetype = S
trigger1 = ctrl
trigger2 = (stateno = 220) && time > 3
trigger2 = movehit





;立ち弱パンチ
[State -1, Stand Light Punch]
type = ChangeState
value = 200
triggerall   = var(59)  = [0,1]
triggerall = command = "x"
triggerall = command != "holddown"
trigger1 = statetype = S
trigger1 = ctrl
;;;trigger2 = (stateno = 230) && time > 27
;;;trigger3 = (stateno = 200) && time > 24







;特殊強パンチ
[State -1]
type = ChangeState
value = 209
triggerall   = var(59)  = [0,1]
triggerall = command = "y"
triggerall = command = "holdfwd"

trigger1 = statetype = S
trigger1 = ctrl

trigger2 = (stateno = 210) && time > 15
trigger2 = movehit

trigger3 = stateno = 199;;特殊弱パンチ1
trigger3 = movehit

trigger4 = stateno = 198;;特殊弱パンチ2
trigger4 = movehit

trigger5 = stateno = 229;;特殊弱キック1
trigger5 = movehit








;立ち強パンチ
[State -1, Stand Strong Punch]
type = ChangeState
value = 210
triggerall   = var(59)  = [0,1]
triggerall = command = "y"
triggerall = command != "holddown"
triggerall = command != "holdfwd"

trigger1 = statetype = S
trigger1 = ctrl

trigger2 = (stateno = 240) && time > 12
trigger2 = movehit

trigger3 = stateno = 199;;特殊弱パンチ1
trigger3 = movehit

trigger4 = stateno = 198;;特殊弱パンチ2
trigger4 = movehit

trigger5 = stateno = 229;;特殊弱キック1
trigger5 = movehit




;------------------------------------------------------------------------------



;特殊弱キック
[State -1]
type = ChangeState
value = 229
triggerall   = var(59)  = [0,1]
triggerall = command = "a"
triggerall = command = "holdfwd"

trigger1 = statetype = S
trigger1 = ctrl

trigger2 = (stateno = 230) && time > 3
trigger2 = movehit











;立ち弱キック
[State -1, Stand Light Kick]
type = ChangeState
value = 230
triggerall   = var(59)  = [0,1]
triggerall = command = "a"
triggerall = command != "holddown"
trigger1 = statetype = S
trigger1 = ctrl
trigger2 = (stateno = 200) && time > 24
trigger3 = (stateno = 230) && time > 27









;特殊強キック
[State -1]
type = ChangeState
value = 239
triggerall   = var(59)  = [0,1]
triggerall = command = "b"
triggerall = command = "holdfwd"
trigger1 = statetype = S
trigger1 = ctrl
trigger2 = (stateno = 240) && time > 15
trigger2 = movehit


trigger3 = stateno = 199;;特殊弱パンチ1
trigger3 = movehit

trigger4 = stateno = 198;;特殊弱パンチ2
trigger4 = movehit

trigger5 = stateno = 229;;特殊弱キック1
trigger5 = movehit







;立ち強キック
[State -1, Standing Strong Kick]
type = ChangeState
value = 240
triggerall   = var(59)  = [0,1]
triggerall = command = "b"
triggerall = command != "holddown"

trigger1 = statetype = S
trigger1 = ctrl

trigger2 = (stateno = 210) && time > 12
trigger2 = movehit

trigger3 = stateno = 199;;特殊弱パンチ1
trigger3 = movehit

trigger4 = stateno = 198;;特殊弱パンチ2
trigger4 = movehit

trigger5 = stateno = 229;;特殊弱キック1
trigger5 = movehit





;------------------------------------------------------------------------------
;挑発
[State -1, Taunt]
type = ChangeState
value = 195
triggerall   = var(59)  = [0,1]
triggerall = command = "start"
trigger1 = statetype != A
trigger1 = ctrl

;------------------------------------------------------------------------------
;------------------------------------------------------------------------------
;しゃがみ弱パンチ
[State -1, Crouching Light Punch]
type = ChangeState
value = 400
triggerall   = var(59)  = [0,1]
triggerall = command = "x"
triggerall = command = "holddown"
trigger1 = statetype = C
trigger1 = ctrl

;しゃがみ強パンチ
[State -1, Crouching Strong Punch]
type = ChangeState
value = 410
triggerall   = var(59)  = [0,1]
triggerall = command = "y"
triggerall = command = "holddown"
trigger1 = statetype = C
trigger1 = ctrl
trigger2 = (stateno = 400) || (stateno = 430)
trigger2 = (time > 9) || (movecontact && time > 5)

;------------------------------------------------------------------------------
;しゃがみ弱キック
[State -1, Crouching Light Kick]
type = ChangeState
value = 430
triggerall   = var(59)  = [0,1]
triggerall = command = "a"
triggerall = command = "holddown"
trigger1 = statetype = C
trigger1 = ctrl
trigger2 = (stateno = 400) || (stateno = 430)
trigger2 = (time > 9) || (movecontact && time > 4)

;しゃがみ強キック
[State -1, Crouching Strong Kick]
type = ChangeState
value = 440
triggerall   = var(59)  = [0,1]
triggerall = command = "b"
triggerall = command = "holddown"
trigger1 = statetype = C
trigger1 = ctrl
trigger2 = (stateno = 400) || (stateno = 430)
trigger2 = (time > 9) || (movecontact && time > 5)

;------------------------------------------------------------------------------
;------------------------------------------------------------------------------
;空中弱パンチ
[State -1, Jump Light Punch]
type = ChangeState
value = 600
triggerall   = var(59)  = [0,1]
triggerall = command = "x"
trigger1 = statetype = A
trigger1 = ctrl
trigger2 = stateno = 600
trigger2 = statetime >= 7

;空中強パンチ
[State -1, Jump Strong Punch]
type = ChangeState
value = 610
triggerall   = var(59)  = [0,1]
triggerall = command = "y"
trigger1 = statetype = A
trigger1 = ctrl
trigger2 = stateno = 600 || stateno = 630
trigger2 = movecontact

;------------------------------------------------------------------------------
;空中弱キック
[State -1, Jump Light Kick]
type = ChangeState
value = 630
triggerall   = var(59)  = [0,1]
triggerall = command = "a"
trigger1 = statetype = A
trigger1 = ctrl

;空中強キック
[State -1, Jump Strong Kick]
type = ChangeState
value = 640
triggerall   = var(59)  = [0,1]
triggerall = command = "b"
trigger1 = statetype = A
trigger1 = ctrl
trigger2 = stateno = 600 || stateno = 630
trigger2 = movecontact








;------------------------------------------------------------------------------
;------------------------------------------------------------------------------
;------------------------------------------------------------------------------
;------------------------------------------------------------------------------
;--------------------------------------------------------




;;;;;;;追加技;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;







;制空竜巻蹴り
[State -1, kuutyuuh]
type = ChangeState
value = 6760
triggerall   = var(59)  = [0,1]

triggerall = command = "kuutyuuh"
triggerall = power >= 1000 
triggerall = stateno != 6060   ;ウルスラ
triggerall = stateno != 6002   ;超連続攻撃
triggerall = stateno != 6470   ;アニメパンチ 
triggerall = stateno != 6471   ;アニメパンチ
triggerall = stateno != 800    ;投げ
triggerall = stateno != 810    ;投げ
trigger1 = ctrl 
trigger2 = hitdefattr = SC, NA, SA, HA  
trigger3 = MoveContact = 1




;竜子キック
[State -1, r-k]
type = ChangeState
value = 8040
triggerall   = var(59)  = [0,1]

triggerall = command = "r-k"
triggerall = power >= 1000 
triggerall = statetype != A
triggerall = stateno != 6460   ;情熱の 
triggerall = stateno != 6600   ;情熱の 
triggerall = stateno != 6060   ;ウルスラ
triggerall = stateno != 6002   ;超連続攻撃
triggerall = stateno != 6710   ;空中旋風脚 
triggerall = stateno != 6760   ;空中超必
triggerall = stateno != 6470   ;アニメパンチ 
triggerall = stateno != 6471   ;アニメパンチ
triggerall = stateno != 800    ;投げ
triggerall = stateno != 810    ;投げ
trigger1 = ctrl 
trigger2 = hitdefattr = SC, NA, SA, HA  
trigger3 = MoveContact = 1






;超稲妻弾
[State -1]
type = ChangeState
value = 7999
triggerall   = var(59)  = [0,1]
triggerall = command = "superhadou"
triggerall = statetype != A
triggerall = power >= 1000 
trigger1 = ctrl
trigger2 = hitdefattr = SC, NA, SA, HA  
trigger3 = MoveContact = 1




;竜子コレダー
[State -1]
type = ChangeState
value = 8500
triggerall   = var(59)  = [0,1]
triggerall = command = "raigeki"
triggerall = statetype != A
trigger1 = ctrl
trigger2 = MoveContact = 1





;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;WORKS作成　　技






;雷撃
;[State -1, raigeki]
;type = ChangeState
;value = 7800
;triggerall   = var(59)  = [0,1]

;triggerall = command = "raigeki"
;triggerall = statetype != A
;triggerall = stateno != 6460   ;情熱の 
;triggerall = stateno != 6600   ;情熱の 
;triggerall = stateno != 6060   ;ウルスラ
;triggerall = stateno != 6002   ;超連続攻撃
;triggerall = stateno != 6470   ;アニメパンチ 
;triggerall = stateno != 6471   ;アニメパンチ
;triggerall = stateno != 3050   ;スマッシュアッパー 
;triggerall = stateno != 3051   ;スマッシュアッパー 
;triggerall = stateno != 3000   ;三烈突き手 
;triggerall = stateno != 7999   ;スーパー波動拳
;triggerall = stateno != 6760   ;空中超必
;triggerall = stateno != 8040   ;竜子キック
;triggerall = stateno != 8041   ;竜子キック
;triggerall = stateno != 8042   ;竜子キック
;triggerall = stateno != 7200   ;竜子投げ大爆発
;triggerall = stateno != 7400   ;竜子投げ大爆発
;triggerall = stateno != 7600   ;竜子投げ大爆発
;triggerall = stateno != 800    ;投げ
;triggerall = stateno != 810    ;投げ
;trigger1 = ctrl
;trigger2 = MoveContact = 1




;竜子投げ大爆発
[State -1]
type = ChangeState
value = 7200
triggerall   = var(59)  = [0,1]
triggerall = command = "otosi"
triggerall = statetype != A 
triggerall = stateno != 6460   ;情熱の 
triggerall = stateno != 6600   ;情熱の 
triggerall = stateno != 6060   ;ウルスラ
triggerall = stateno != 6002   ;超連続攻撃
triggerall = stateno != 6470   ;アニメパンチ 
triggerall = stateno != 6471   ;アニメパンチ 
triggerall = stateno != 3050   ;スマッシュアッパー 
triggerall = stateno != 3051   ;スマッシュアッパー 
triggerall = stateno != 3000   ;三烈突き手 
triggerall = stateno != 7999   ;スーパー波動拳
triggerall = stateno != 6760   ;空中超必
triggerall = stateno != 8040   ;竜子キック
triggerall = stateno != 8041   ;竜子キック
triggerall = stateno != 8042   ;竜子キック
triggerall = stateno != 1100   ;アッパー 
triggerall = stateno != 1110   ;アッパー 
triggerall = stateno != 1020   ;突き手 NEW
triggerall = stateno != 6040   ;竜巻 
triggerall = stateno != 6400   ;旋風脚 
triggerall = stateno != 6710   ;空中旋風脚 
triggerall = stateno != 7800   ;雷撃 
triggerall = stateno != 7200   ;竜子投げ大爆発
triggerall = stateno != 7400   ;竜子投げ大爆発
triggerall = stateno != 7600   ;竜子投げ大爆発
triggerall = stateno != 800    ;投げ
triggerall = stateno != 810    ;投げ
triggerall = stateno != 1050   ;ヒザ蹴り
triggerall = stateno != 1060   ;ヒザ蹴り
trigger1 = ctrl
trigger2 = MoveContact = 1



;空中ダッシュ
[State -1, Dash]
type = ChangeState
value = 7900
triggerall   = var(59)  = [0,1]
trigger1 = command = "FF"
trigger1 = statetype = A
trigger1 = ctrl


