from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    AWS_SERVER_PUBLIC_KEY: str
    AWS_SERVER_SECRET_KEY: str
    AWS_SESSION_TOKEN: str
    AWS_PROFILE_NAME: str
    REGION_NAME: str
    MODEL_ID: str

    ELEVENLABS_ACCESS_KEY: str
    ELEVENLABS_VOICE_ID: str = "pNInz6obpgDQGcFmaJgB"
    ELEVENLABS_MODEL_NAME: str = "eleven_multilingual_v2"

    WHISPER_LANG_CODES: list = (
        "af,am,ar,as,az,ba,be,bg,bn,bo,br,bs,ca,cs,cy,da,de,el,en,es,et,eu,fa,fi,fo,fr,gl,gu,ha,"
        "haw,he,hi,hr,ht,hu,hy,id,is,it,ja,jw,ka,kk,km,kn,ko,la,lb,ln,lo,lt,lv,mg,mi,mk,ml,mn,mr,ms,"
        "mt,my,ne,nl,nn,no,oc,pa,pl,ps,pt,ro,ru,sa,sd,si,sk,sl,sn,so,sq,sr,su,sv,sw,ta,te,tg,th,tk,tl,tr,"
        "tt,uk,ur,uz,vi,yi,yo,zh"
    ).split(",")

    model_config = SettingsConfigDict(env_file=".env")


settings = AppSettings()
