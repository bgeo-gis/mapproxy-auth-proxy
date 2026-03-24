FROM golang:1.22 AS build

WORKDIR /src

COPY go.mod ./
COPY go.sum ./
RUN go mod download

COPY cmd ./cmd

RUN CGO_ENABLED=0 GOOS=linux go build -trimpath -ldflags="-s -w" -o /out/mapproxy-auth-proxy ./cmd/mapproxy-auth-proxy


FROM gcr.io/distroless/static-debian12:nonroot

ENV PORT=9090
EXPOSE 9090

COPY --from=build /out/mapproxy-auth-proxy /mapproxy-auth-proxy

USER nonroot:nonroot

ENTRYPOINT ["/mapproxy-auth-proxy"]
