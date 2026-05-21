# 기여 가이드

Conventional commit을 사용하고 public identifier는 영어 code identifier로 유지한다. 사용자-facing 문서는 한글로 작성하며, 공식 API 원문이나 identifier가 필요한 경우에만 영어를 보존한다.

## 문서 언어 정책

이 저장소의 모든 Markdown/RST 문서는 한글로 작성한다. 공식 API field, code identifier, 명령어, URL, provider 원문은 필요한 경우 원문을 유지한다.

## PR 전 확인

```bash
ruff check .
mypy src/krheritage
pytest
```

Project owner가 현재 no-PyPI 결정을 바꾸기 전에는 PyPI publishing 설정을 추가하지 않는다.
