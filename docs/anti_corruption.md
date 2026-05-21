# Anti-corruption 메모

알려진 endpoint 이동은 `krheritage.transport._aliases`에서 해결한다.

| Old URL | New URL |
| --- | --- |
| `https://apis.data.go.kr/1550246/recodeImageView` | `https://apis.data.go.kr/1550246/recordImageView` |

Legacy URL을 호출하면 `DeprecationWarning`을 발생시키고 replacement URL을 반환한다.
